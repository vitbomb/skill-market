# Criptografia das mensagens

O backend usa AES-256-GCM, IV aleatório de 12 bytes por mensagem e autenticação
do conteúdo e dos IDs da conversa e do remetente. O banco armazena IV, tag e
cifra em Base64; participantes recebem o texto pela API após autorização.
Isto não é criptografia de ponta a ponta: quem controla servidor e chave pode ler.
Metadados (participantes, datas, remetentes e leituras) continuam legíveis.

## Antes de publicar

1. Faça um backup do banco no Neon. Guarde-o com acesso restrito, pois o histórico
   anterior e os backups antigos ainda contêm texto legível.
2. Gere uma chave no terminal, na sua máquina:
   `node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"`
3. No Render, serviço da API > Environment, adicione `CHAT_ENCRYPTION_KEY`
   com os 64 caracteres gerados. Guarde uma cópia em um gerenciador de senhas.
   Nunca coloque essa chave no GitHub, frontend, Vercel ou em capturas de tela.
4. Publique as alterações no repositório acompanhado pelo Render.

A chave é obrigatória: sem ela, ou com formato incorreto, a API não inicia.
Ao iniciar, antes de atender requisições, o backend bloqueia a tabela de mensagens,
adiciona a coluna de versão, converte o histórico e ajusta sua restrição de tamanho
em uma transação. O usuário do banco precisa poder alterar a tabela.
Não é preciso executar SQL manualmente. As tabelas do chat já devem existir
(para um banco novo, execute primeiro migrations/001_chat.sql).

Nos próximos reinícios, verifica as mensagens já cifradas com a chave atual.
Uma falha desfaz a transação e impede a inicialização. A implementação carrega
o histórico na memória durante essa verificação, adequada ao volume do projeto
escolar; um histórico grande exige migração em lotes e controle de versões separado.

## Depois de publicar

Envie uma mensagem com uma conta e leia com a outra. Confira também a prévia
na lista de conversas e o histórico anterior. No Neon, o campo `conteudo` deve
estar ilegível e `criptografia` deve ser 1. Não compartilhe o conteúdo real.

Não troque nem apague a chave: isso impede a leitura do histórico. Rotação exige
uma migração planejada usando a chave anterior e a nova. Não reverta para o
backend antigo após a migração, pois ele não sabe ler os dados cifrados.
Durante o deploy, evite uso do chat: instâncias da versão anterior podem falhar
ao enviar ou exibir cifras até serem substituídas.

Vercel e Brevo não precisam de configuração adicional. O navegador continua
usando as mesmas rotas e campos. HTTPS, controle de acesso ao Render/Neon,
política de retenção e privacidade continuam necessários.

## Verificação local

Na pasta backend, execute `npm test`. Os testes cobrem Unicode, limite,
IV aleatório, adulteração, chave incorreta, contexto, migração e rollback.
