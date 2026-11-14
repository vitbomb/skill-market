const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const crypto = require('node:crypto');

// Executa as rotas reais sem abrir portas ou acessar o banco de produção.
function carregar(secret = 'ab'.repeat(32), statusPerfil = 'pendente', intencao = 'Contratar e oferecer') {
    const routes = new Map();
    const queries = [];
    const senhasHash = [];
    let emailVerificado = false;
    const app = { use() {}, listen() {} };
    for (const method of ['get', 'post', 'patch']) {
        app[method] = (path, ...handlers) => routes.set(`${method} ${path}`, handlers);
    }
    const express = () => app;
    express.json = express.urlencoded = () => () => {};
    const tokens = { dono: { id: 7 }, outro: { id: 8 }, admin: { role: 'admin' }, semId: {}, idInvalido: { id: 'abc' } };
    const pool = {
        async query(sql, args) {
            queries.push({ sql, args });
            if (sql === 'SELECT intencao FROM usuarios WHERE id = $1') return { rows: [{ intencao }] };
            if (sql.includes('RETURNING id, email')) {
                assert.match(sql, /codigo_verificacao = \$2 AND verificado = FALSE/);
                if (emailVerificado || args[1] !== '123456') return { rows: [] };
                emailVerificado = true;
                return { rows: [{ id: 7, email: args[0] }] };
            }
            if (sql.includes('WHERE LOWER(email)')) return { rows: [{ id: 7, verificado: true }] };
            if (sql.includes('SELECT * FROM usuarios WHERE token_recuperacao')) return { rows: [{ id: 7 }] };
            if (sql.includes('INSERT INTO perfis')) return { rows: [{ id: 1 }] };
            if (sql.includes('p.usuario_id = $1')) {
                assert.match(sql, /p\.status = 'aprovado' OR \$2::boolean/);
                return { rows: (statusPerfil === 'aprovado' || args[1]) ? [{ usuario_id: 7, status: statusPerfil }] : [] };
            }
            return { rows: [] };
        },
        end() {}
    };
    const modules = {
        dotenv: { config() {} }, express, cors: () => () => {},
        bcryptjs: { hash: async senha => { senhasHash.push(senha); return 'hash-simulado'; } }, crypto,
        jsonwebtoken: { sign(payload, key, options) {
            assert.equal(payload.id, 7);
            assert.equal(key, secret);
            assert.equal(options.expiresIn, '4h');
            return 'dono';
        }, verify(token, key, options) {
            assert.equal(key, secret);
            assert.deepEqual(Array.from(options.algorithms), ['HS256']);
            if (!tokens[token]) throw new Error('Token inválido');
            return tokens[token];
        } },
        './database': { pool, testarConexao: async () => {} },
        './chat-crypto': { criarCriptografia: () => ({}), migrarMensagens: async () => {} }
    };
    vm.runInNewContext(fs.readFileSync(`${__dirname}/server.js`, 'utf8'), {
        require: name => { if (!(name in modules)) throw new Error(name); return modules[name]; },
        process: { env: { JWT_SECRET: secret } }, Buffer, console
    });
    return {
        queries,
        senhasHash,
        async request(method, path, token, body = {}, query = {}) {
            const req = { headers: token ? { authorization: `Bearer ${token}` } : {}, body, params: { usuario_id: '7' }, query };
            const res = { code: 200, status(code) { this.code = code; return this; }, json(data) { this.data = data; return this; } };
            const handlers = routes.get(`${method} ${path}`);
            async function run(index) {
                if (handlers[index]) await handlers[index](req, res, () => run(index + 1));
            }
            await run(0);
            return res;
        }
    };
}

test('JWT exige configuração e rejeita segredo vazio, curto ou antigo', () => {
    for (const secret of [undefined, '', 'curto', ' '.repeat(40), 'chave_seguranca_skillmarket']) {
        // undefined usa o argumento padrão; representa ausência com null.
        assert.throws(() => carregar(secret === undefined ? null : secret), /JWT_SECRET/);
    }
});

test('gravação exige usuário autenticado e ignora ID e status enviados no corpo', async () => {
    const api = carregar();
    for (const token of [undefined, 'invalido', 'admin', 'semId', 'idInvalido']) {
        assert.equal((await api.request('post', '/api/perfil', token)).code, 401);
    }
    assert.equal(api.queries.length, 0);
    assert.equal((await api.request('post', '/api/perfil', 'dono', { usuario_id: 8, status: 'aprovado' })).code, 200);
    assert.equal(api.queries[0].args[0], 7);
    assert.match(api.queries.find(q => q.sql.includes('INSERT INTO perfis')).sql, /status = 'pendente'/);
});

for (const status of ['pendente', 'rejeitado']) test(`perfil ${status} só pode ser lido pelo dono ou administrador`, async () => {
    const api = carregar('ab'.repeat(32), status);
    for (const token of [undefined, 'outro']) {
        assert.equal((await api.request('get', '/api/perfil/:usuario_id', token)).code, 404);
    }
    for (const token of ['dono', 'admin']) {
        assert.equal((await api.request('get', '/api/perfil/:usuario_id', token)).data.status, status);
    }
    const count = api.queries.length;
    assert.equal((await api.request('get', '/api/perfil/:usuario_id', 'invalido')).code, 401);
    assert.equal(api.queries.length, count);
});

test('perfil aprovado continua público', async () => {
    const api = carregar('ab'.repeat(32), 'aprovado');
    assert.equal((await api.request('get', '/api/perfil/:usuario_id')).data.status, 'aprovado');
});

test('listagem pública mantém filtro de aprovação, inclusive com busca', async () => {
    const api = carregar();
    await api.request('get', '/api/perfis');
    assert.match(api.queries[0].sql, /WHERE p\.status = 'aprovado'/);
    assert.match(api.queries[0].sql, /u\.intencao IS DISTINCT FROM 'Apenas contratar'/);
    await api.request('get', '/api/perfis', undefined, {}, { busca: 'eletricista' });
    assert.match(api.queries[1].sql, /WHERE p\.status = 'aprovado'/);
    assert.equal(api.queries[1].args[0], '%eletricista%');
});

test('contratante salva somente foto, nome e localização, descartando campos profissionais', async () => {
    const api = carregar('ab'.repeat(32), 'pendente', 'Apenas contratar');
    const res = await api.request('post', '/api/perfil', 'dono', {
        nome_completo: 'Cliente', localizacao: 'Toledo', foto_perfil: 'foto',
        area_atuacao: 'Cargo', sobre_voce: 'Bio', qualidades: 'Habilidade', telefone: '123',
        instagram: '@teste', email_contato: 'teste@example.com', site: 'site', fotos: 'portfolio'
    });
    assert.equal(res.code, 200);
    const valores = api.queries.find(q => q.sql.includes('INSERT INTO perfis')).args;
    assert.equal(valores[1], 'Cliente');
    assert.equal(valores[3], 'Toledo');
    assert.equal(valores[11], 'foto');
    for (const i of [2, 4, 5, 6, 7, 8, 9, 10]) assert.equal(valores[i], '');
});

for (const path of ['/api/signup', '/api/redefinir-senha']) {
    const body = senha => ({ nome: 'Teste', email: 'teste@example.com', senha, novaSenha: senha, token: 'recuperacao' });
    test(`${path} bloqueia senhas curtas antes de consultar ou alterar o banco`, async () => {
        const api = carregar();
        for (const senha of ['', 'a'.repeat(14), '😀'.repeat(14), undefined, 123456789012345]) {
            assert.equal((await api.request('post', path, undefined, body(senha))).code, 400);
        }
        assert.equal(api.queries.length, 0);
        assert.equal(api.senhasHash.length, 0);
    });
    test(`${path} aceita 15 caracteres sem exigir composição e preserva espaços`, async () => {
        const api = carregar();
        for (const senha of ['a'.repeat(15), '1'.repeat(15), '😀'.repeat(15), 'uma frase bem longa', '  uma frase longa  ']) {
            const res = await api.request('post', path, undefined, body(senha));
            // No cadastro, a conta simulada já existe. A política passou antes do 409.
            assert.equal(res.code, path === '/api/signup' ? 409 : 200);
            assert.equal(api.senhasHash.at(-1), senha);
        }
    });
}

test('verificação cria sessão para salvar o perfil e impede reutilizar o código', async () => {
    const api = carregar();
    for (const codigo of ['', 'abc', '000000']) {
        const res = await api.request('post', '/api/verificar-codigo', undefined, { email: 'teste@example.com', codigo });
        assert.equal(res.code, 400);
        assert.equal(res.data.token, undefined);
    }
    const body = { email: 'teste@example.com', codigo: '123456' };
    const res = await api.request('post', '/api/verificar-codigo', undefined, body);
    assert.equal(res.code, 200);
    assert.equal(res.data.usuarioId, 7);
    assert.equal((await api.request('post', '/api/perfil', res.data.token)).code, 200);
    assert.equal((await api.request('post', '/api/verificar-codigo', undefined, body)).code, 400);
});
