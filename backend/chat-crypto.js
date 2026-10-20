const crypto = require('node:crypto');

function criarCriptografia(valor = process.env.CHAT_ENCRYPTION_KEY) {
    if (!/^[a-fA-F0-9]{64}$/.test(valor || '')) {
        throw new Error('Configure CHAT_ENCRYPTION_KEY com 64 caracteres hexadecimais (32 bytes).');
    }
    const chave = Buffer.from(valor, 'hex');
    const contexto = (conversa, remetente) => Buffer.from(`skillmarket:chat:v1:${conversa}:${remetente}`);
    return {
        cifrar(texto, conversa, remetente) {
            const iv = crypto.randomBytes(12);
            const cipher = crypto.createCipheriv('aes-256-gcm', chave, iv);
            cipher.setAAD(contexto(conversa, remetente));
            const dados = Buffer.concat([cipher.update(texto, 'utf8'), cipher.final()]);
            return Buffer.concat([iv, cipher.getAuthTag(), dados]).toString('base64');
        },
        decifrar(valor, conversa, remetente) {
            const dados = Buffer.from(valor, 'base64');
            if (dados.length < 29) throw new Error('Mensagem criptografada inválida.');
            const decipher = crypto.createDecipheriv('aes-256-gcm', chave, dados.subarray(0, 12));
            decipher.setAAD(contexto(conversa, remetente));
            decipher.setAuthTag(dados.subarray(12, 28));
            return Buffer.concat([decipher.update(dados.subarray(28)), decipher.final()]).toString('utf8');
        }
    };
}

// Executada antes de aceitar requisições; uma falha desfaz toda a conversão.
async function migrarMensagens(pool, criptografia) {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        await client.query('LOCK TABLE mensagens IN ACCESS EXCLUSIVE MODE');
        await client.query('ALTER TABLE mensagens ADD COLUMN IF NOT EXISTS criptografia SMALLINT NOT NULL DEFAULT 0');
        await client.query('ALTER TABLE mensagens DROP CONSTRAINT IF EXISTS mensagens_conteudo_valido');
        const resultado = await client.query('SELECT id, conversa_id, remetente_id, conteudo, criptografia FROM mensagens');
        for (const msg of resultado.rows) {
            if (msg.criptografia === 1) {
                // Também impede iniciar com uma chave diferente da usada no histórico.
                criptografia.decifrar(msg.conteudo, msg.conversa_id, msg.remetente_id);
            } else if (msg.criptografia === 0) {
                const cifrada = criptografia.cifrar(msg.conteudo, msg.conversa_id, msg.remetente_id);
                await client.query('UPDATE mensagens SET conteudo = $1, criptografia = 1 WHERE id = $2', [cifrada, msg.id]);
            } else {
                throw new Error('Versão de criptografia não suportada.');
            }
        }
        await client.query(`ALTER TABLE mensagens ADD CONSTRAINT mensagens_conteudo_valido
            CHECK (criptografia = 1 AND char_length(conteudo) BETWEEN 40 AND 12000)`);
        await client.query('COMMIT');
    } catch (erro) {
        await client.query('ROLLBACK');
        throw erro;
    } finally {
        client.release();
    }
}

module.exports = { criarCriptografia, migrarMensagens };
