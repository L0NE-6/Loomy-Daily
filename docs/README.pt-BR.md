# 🌙 Loomy Daily

Atualiza os pontos de presente diários do Loomy e resgata recompensas de oito tarefas de integração. A automação usa um único script Python e suporta várias contas.

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

A documentação completa em chinês está em [../README.md](../README.md).

## Recursos

- Chama a API de primeiro login diário para atualizar os pontos de presente de forma idempotente.
- Envia as oito tarefas de integração e acompanha até 10000 pontos.
- Salva um snapshot local depois que todas as tarefas são concluídas.
- Oferece `--tasks`, `--claim KEY` e `--refresh` para consulta, resgate individual e nova leitura forçada.
- Suporta login por SMS e várias sessions separadas por linha ou `&`.
- Suporta notificações por PushPlus, Bark, WeCom, DingTalk e Qinglong.

## Início rápido no Qinglong

```bash
python3 -m pip install -r requirements.txt
```

Envie `loomy_daily.py`, configure `LOOMY_TOKENS` e crie a tarefa:

```text
45 8 * * * task loomy_daily.py
```

Para desativar as tarefas de integração:

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

Para criar uma session:

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note principal
python loomy_login.py --verify
```

## GitHub Actions

Crie os Secrets em **Settings → Secrets and variables → Actions**:

```text
LOOMY_TOKENS
PUSHPLUS_TOKEN          # opcional
BARK_URL                # opcional
WECOM_WEBHOOK           # opcional
DINGTALK_WEBHOOK        # opcional
DINGTALK_SECRET         # opcional
```

Execute **Actions → Loomy Daily → Run workflow**. O workflow é manual por padrão. Ative o agendamento comentado em `.github/workflows/daily.yml` quando necessário; o cron usa UTC.

## Variáveis principais

| Variável | Uso |
| :--- | :--- |
| `LOOMY_TOKENS` | Obrigatória. Use `session` ou `note\|session`; separe contas por linha ou `&`. |
| `LOOMY_ONBOARDING` | Valor padrão `1`; use `0` para ignorar as tarefas de integração. |
| `PUSHPLUS_TOKEN`, `BARK_URL`, `WECOM_WEBHOOK`, `DINGTALK_WEBHOOK`, `DINGTALK_SECRET` | Canais de notificação opcionais |
| `QL_URL`, `QL_TOKEN` | Endpoint opcional do Qinglong e token legado do painel |

## Sucesso e privacidade

O presente diário é confirmado quando a API retorna o código de negócio `000000`; o script mostra `dailyBalance` quando disponível. Sucesso novo, tarefa já concluída e falha são reportados separadamente, com confirmação pela lista de tarefas.

`loomy_login_result.json` contém telefone e session. `loomy_onboarding.json` contém progresso e um fingerprint de session em uma direção. Ambos são ignorados pelo Git. Não publique session, telefone ou arquivos locais em uma issue.

## Limites de uso e redistribuição

As versões oficiais deste projeto são gratuitas, incluindo o repositório, os scripts, as instruções de implantação e os Releases.

Sem autorização escrita explícita do autor, não empacote o projeto como recurso pago, edição interna ou exclusiva, benefício de assinatura, curso pago, implantação paga ou serviço de atualização; não o republique em contas, grupos ou canais sem relação para gerar tráfego ou captar usuários; não remova avisos de autoria e direitos autorais nem reivindique o trabalho como seu; não use o nome, avatar, QR codes ou nome do projeto para sugerir endosso oficial.

Em caso de violação, o autor pode solicitar a remoção do conteúdo e pode pausar atualizações, arquivar ou excluir o repositório. Consulte [NOTICE.md](../NOTICE.md) para as regras completas.

## Links

- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)
- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [Código e guia completo em chinês](../README.md)
