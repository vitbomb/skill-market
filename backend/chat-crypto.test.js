const { test } = require('node:test');
const assert = require('node:assert/strict');
const { criarCriptografia, migrarMensagens } = require('./chat-crypto');
const chave = 'ab'.repeat(32);
const cryptoChat = criarCriptografia(chave);

test('exige uma chave de 256 bits em hexadecimal', () => {
    for (const invalida of ['', 'segredo', 'zz'.repeat(32), 'ab'.repeat(31)]) {
        assert.throws(() => criarCriptografia(invalida));
    }
});

test('preserva Unicode e limite de 2000 caracteres, sem repetir cifra', () => {
    for (const texto of ['Olá, João! 🔒', '界'.repeat(2000)]) {
        const a = cryptoChat.cifrar(texto, '1', '2');
        assert.notEqual(a, cryptoChat.cifrar(texto, 1, 2));
        assert.equal(cryptoChat.decifrar(a, 1, 2), texto);
        assert.ok(a.length <= 12000);
        assert.ok(!a.includes(texto));
    }
});

test('rejeita adulteração, chave errada e troca de conversa ou remetente', () => {
    const cifrada = cryptoChat.cifrar('Privado', 1, 2);
    const bytes = Buffer.from(cifrada, 'base64');
    bytes[bytes.length - 1] ^= 1;
    assert.throws(() => cryptoChat.decifrar(bytes.toString('base64'), 1, 2));
    assert.throws(() => criarCriptografia('cd'.repeat(32)).decifrar(cifrada, 1, 2));
    assert.throws(() => cryptoChat.decifrar(cifrada, 3, 2));
    assert.throws(() => cryptoChat.decifrar(cifrada, 1, 3));
});

function bancoSimulado(rows) {
    const chamadas = [];
    const client = {
        async query(sql, args) {
            chamadas.push({ sql, args });
            return { rows: sql.startsWith('SELECT') ? rows : [] };
        },
        release() { chamadas.push({ sql: 'RELEASE' }); }
    };
    return { pool: { connect: async () => client }, chamadas };
}

test('converte texto antigo e verifica histórico cifrado sem cifrar duas vezes', async () => {
    const banco = bancoSimulado([
        { id: 1, conversa_id: 4, remetente_id: 2, conteudo: 'Histórico', criptografia: 0 },
        { id: 2, conversa_id: 4, remetente_id: 2, conteudo: cryptoChat.cifrar('Nova', 4, 2), criptografia: 1 }
    ]);
    await migrarMensagens(banco.pool, cryptoChat);
    const updates = banco.chamadas.filter(c => c.sql.startsWith('UPDATE'));
    assert.equal(updates.length, 1);
    assert.equal(cryptoChat.decifrar(updates[0].args[0], 4, 2), 'Histórico');
    assert.ok(banco.chamadas.some(c => c.sql === 'COMMIT'));
});

test('falha de autenticação desfaz a migração e libera a conexão', async () => {
    const banco = bancoSimulado([
        { id: 1, conversa_id: 4, remetente_id: 2, conteudo: 'Antiga', criptografia: 0 },
        { id: 2, conversa_id: 4, remetente_id: 2, conteudo: 'inválida', criptografia: 1 }
    ]);
    await assert.rejects(migrarMensagens(banco.pool, cryptoChat));
    assert.ok(banco.chamadas.some(c => c.sql === 'ROLLBACK'));
    assert.ok(!banco.chamadas.some(c => c.sql === 'COMMIT'));
    assert.equal(banco.chamadas.at(-1).sql, 'RELEASE');
});
