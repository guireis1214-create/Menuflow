# MenuFlow — protótipo multi-perfil

## Perfis de demonstração
- Administrador de restaurante: `admin / 123456`
- Cliente: `cliente / 123456`
- Programador/suporte MenuFlow: `suporte / 123456`

## Fluxos acrescentados
- Central de suporte para acompanhar cadastros de restaurantes, aprovar, suspender e manter pendente.
- Formulário de solicitação de cadastro do estabelecimento (nome, responsável, e-mail, telefone e endereço).
- Cadastro de conta de cliente (nome, e-mail e telefone).
- Cliente vê lista de estabelecimentos aprovados e cardápio/pedido de demonstração.
- Persistência SQLite para estabelecimentos e clientes.

## Executar
Na pasta backend: `pip install -r requirements.txt` e `uvicorn main:app --reload`. Acesse `http://127.0.0.1:8000`.

**Aviso:** protótipo didático, com login demonstrativo e endpoints ainda não protegidos. Aprovação de restaurantes não implementa ainda tenancy (isolamento de dados), autenticação segura, papéis por restaurante, catálogo/menu por estabelecimento, nem cobrança. Não usar em produção antes de implementar controles de segurança e revisão.
