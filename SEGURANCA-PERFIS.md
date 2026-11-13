# Correção de segurança dos perfis

Problemas confirmados no código: gravação sem autenticação confiando em `usuario_id` do corpo, segredo JWT padrão e consulta individual sem filtro de aprovação. A listagem `/api/perfis` já filtrava aprovados.

## Publicação

1. No ambiente do backend no Render, configure `JWT_SECRET` com um segredo novo e aleatório. Para gerar um valor de 32 bytes localmente, use `node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"`. Guarde o valor apenas nas variáveis do servidor, nunca no frontend ou no repositório. Use uma chave diferente de `CHAT_ENCRYPTION_KEY`.
2. Publique o backend atualizado. Ele recusa iniciar sem uma `JWT_SECRET` válida de pelo menos 32 bytes e não aceita mais a chave padrão antiga. Mantenha as demais variáveis já configuradas.
3. Publique o frontend atualizado na Vercel para enviar o token nas operações de perfil.
4. Faça login novamente como usuário e administrador: a troca da chave invalida os tokens anteriores.

## Comportamento esperado

- `POST /api/perfil` exige JWT de usuário e usa exclusivamente o ID autenticado. Um ID ou status enviado no corpo não muda o dono nem aprova o perfil. Edições continuam voltando para análise.
- `GET /api/perfil/:usuario_id` permite acesso público somente a aprovados. Perfis pendentes e rejeitados ficam disponíveis ao dono autenticado e ao administrador. Para os demais, responde 404; tokens inválidos ou expirados recebem 401.
- `GET /api/perfis`, com ou sem busca, continua listando apenas aprovados.

## Política de senhas

Cadastro e redefinição exigem pelo menos 15 caracteres, com validação no frontend e no backend. Não há obrigatoriedade de combinar letras maiúsculas, minúsculas, números ou símbolos. Espaços são preservados e caracteres Unicode são contados por pontos de código. A regra se aplica a senhas novas; contas existentes continuam podendo entrar com a senha atual.

Referência: [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), seção Implement Proper Password Strength Controls, consultada em 13/11/2026. Esta alteração atende ao requisito de comprimento mínimo solicitado, sem representar implementação integral de todas as recomendações da OWASP.

## Execução dos testes

Execute `npm test` em `backend`. Os testes das rotas executam o código do servidor com banco e verificador JWT simulados, sem acessar dados de produção. Eles cobrem autenticação, tentativa de trocar o dono, moderação e visibilidade. A publicação e a configuração das variáveis em produção precisam ser verificadas no ambiente de hospedagem.
