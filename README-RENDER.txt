DEPLOY DO MENUFLOW NO RENDER (FRONTEND + API NO MESMO SERVIÇO)

1. Extraia este ZIP.
2. Envie a pasta/projeto para um repositório GitHub.
3. No Render, escolha New + > Blueprint.
4. Conecte o repositório que contém o arquivo render.yaml.
5. O Render criará um Web Service chamado menuflow.
6. Ao terminar, abra a URL gerada pelo Render.

O frontend e a API ficam no mesmo endereço:
- Frontend: https://SEU-SERVICO.onrender.com/
- API de teste: https://SEU-SERVICO.onrender.com/api/health
- Documentação da API: https://SEU-SERVICO.onrender.com/docs

Login de demonstração:
- Usuário: admin
- Senha: 123456

IMPORTANTE:
- O banco SQLite fica no disco persistente /var/data.
- O plano gratuito do Render pode suspender o serviço após inatividade; a primeira abertura pode demorar.
- O login atual é apenas demonstrativo e não é adequado para produção. Troque as credenciais e implemente autenticação segura antes de usar com dados reais.
