"""Generate editable Draw.io, readable SVG and Mermaid from one current-state model."""

import argparse
import html
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/architecture/diagrams"
REFERENCE = "2549523 / 0007_product_operations"


def node(key, label, x, y, width=260, height=130):
    return (key, label, x, y, width, height)


# Coordinates and optional waypoints are shared by both visual exports.
PAGES = [
    (
        "01-System-Context",
        "system-context",
        "Uma loja · personas e dependências atuais",
        [
            node("tutor", "Tutor / CUSTOMER\nPets, reserva e histórico próprios", 60, 180),
            node("staff", "Funcionário / EMPLOYEE\nAgenda e cuidado do dia", 60, 400),
            node("admin", "Administrador / ADMIN\nOperação, gestão e acessos", 60, 620),
            node(
                "petland",
                "PetLand 3.0\nPlataforma operacional de pet shop\nUma loja · monólito modular",
                510,
                400,
                320,
            ),
            node(
                "smtp",
                "SMTP / Mailpit local\nConfirmação, lembrete e pronto\nSem entrega externa comprovada",
                1080,
                180,
            ),
            node("db", "PostgreSQL 17\nArmazenamento interno\nSingle-node", 1080, 400),
            node(
                "ops",
                "Operador offline\nMigrations, backup e recuperação\nArchive e chave no mesmo host",
                1080,
                620,
            ),
        ],
        [
            ("tutor", "petland", "usa", []),
            ("staff", "petland", "usa", []),
            ("admin", "petland", "usa", []),
            ("petland", "smtp", "comunica", []),
            ("petland", "db", "persiste", []),
            ("ops", "db", "opera", []),
        ],
        "PostgreSQL pertence ao sistema. SMTP atual é local; não há provedor externo contratado.",
    ),
    (
        "02-Containers",
        "containers",
        "Staging local · containers e processo de outbox",
        [
            node("react", "Browser / React SPA\nQuery, RHF/Zod, TypeScript", 60, 180),
            node("nginx", "Nginx\nFrontend estático e proxy /api\nHTTPS localhost:8443", 410, 180),
            node("api", "FastAPI\n2 Uvicorn workers\nCasos de uso síncronos", 760, 180),
            node("db", "PostgreSQL 17\nSQLAlchemy / psycopg\nVolume staging_data", 1110, 180),
            node(
                "outbox",
                "Outbox processor\nThread no lifespan de cada worker\nClaim / lease / retry",
                760,
                430,
            ),
            node("smtp", "Mailpit\nSMTP STARTTLS\nUI somente loopback", 1110, 430),
            node(
                "migration",
                "Alembic job\nExecuta antes da API\nCredencial migrator separada",
                410,
                680,
            ),
            node(
                "backup",
                "Ferramentas offline\nBackup autenticado local\nRestore em banco novo",
                760,
                680,
            ),
            node(
                "archive",
                "Archive criptografado\nChave separada / mesmo host\nNão publicado",
                1110,
                680,
            ),
        ],
        [
            ("react", "nginx", "HTTPS", []),
            ("nginx", "api", "/api", []),
            ("api", "db", "TLS / runtime", []),
            ("api", "outbox", "lifespan", []),
            ("outbox", "smtp", "fora da transação", []),
            ("outbox", "db", "claim", [(1055, 495), (1055, 320), (1240, 320)]),
            ("migration", "db", "DDL separado", [(690, 745), (690, 350), (1390, 350), (1390, 245)]),
            ("backup", "archive", "dump / encrypt", []),
            (
                "backup",
                "db",
                "restore isolado",
                [(1040, 745), (1040, 600), (1390, 600), (1390, 245)],
            ),
        ],
        "Outbox é componente dentro da API, não um container ou broker independente. Entrega at least once.",
    ),
    (
        "03-Backend-Modules",
        "backend-modules",
        "Composição, fronteiras e dependências internas",
        [
            node(
                "boot",
                "bootstrap / composition root\nEngine, adapters, serviços e routers",
                60,
                170,
                360,
                100,
            ),
            node(
                "system",
                "system\nSaúde e revisão do schema\nApplication / infrastructure / HTTP",
                60,
                360,
                360,
                150,
            ),
            node(
                "identity",
                "identity\nContas, sessões, papéis, auditoria\nPublic: Actor / HTTP / workforce",
                540,
                170,
                360,
                150,
            ),
            node(
                "customers",
                "customers\nContato e vínculo verificado\nPublic: acesso / contato",
                1020,
                170,
                360,
                150,
            ),
            node(
                "pets",
                "pets\nPropriedade e contexto de cuidado\nPublic: referências / booking",
                1020,
                570,
                360,
                150,
            ),
            node(
                "catalog",
                "catalog\nServiço e oferta por porte\nPublic: booking_service",
                60,
                570,
                360,
                150,
            ),
            node(
                "scheduling",
                "scheduling\nAgenda, reserva, cuidado e gestão\nPublic: coordination / primeiro lock",
                540,
                570,
                360,
                150,
            ),
            node(
                "layers",
                "Camadas nos módulos comerciais: presentation → application → domain\nInfrastructure implementa ports; bootstrap compõe. Public conecta módulos na mesma transação.\nSystem é mínimo, sem domínio comercial. Fitness functions verificam imports absolutos e relativos.",
                60,
                800,
                1320,
                100,
            ),
        ],
        [
            ("boot", "system", "compõe", []),
            ("boot", "identity", "compõe", []),
            ("customers", "identity", "contratos públicos", []),
            ("scheduling", "identity", "Actor / workforce / audit", []),
            ("scheduling", "catalog", "oferta pública", []),
            ("scheduling", "pets", "pet / care context", []),
            ("scheduling", "customers", "contato público", [(960, 645), (960, 400), (1200, 400)]),
        ],
        "Modular Monolith with Hexagonal Architecture and pragmatic DDD principles. Sem microservices / DDD puro.",
    ),
    (
        "04-Booking-Transaction",
        "booking-transaction",
        "Confirmação e garantias transacionais",
        [
            node(
                "review",
                "1 · React / tutor\nConsulta não segura vaga\nResumo + confirmar explicitamente",
                60,
                180,
            ),
            node(
                "request", "2 · HTTP\nSessão + origem / CSRF\nVersões + Idempotency-Key", 410, 180
            ),
            node(
                "lock",
                "3 · Transação\nPrimeiro lock: configuração da loja\nReautoriza ator e proprietário",
                760,
                180,
            ),
            node(
                "validate",
                "4 · Revalidação\nOferta, escala, pessoa, duração\nBuffers, conflitos e pools",
                1110,
                180,
            ),
            node(
                "write",
                "5 · PostgreSQL\nReserva + snapshot + evento\nAuditoria + replay + outbox",
                1110,
                430,
            ),
            node(
                "integrity",
                "6 · GiST / constraints\nExclusão pet e responsável\nCommit ou rollback",
                760,
                430,
            ),
            node(
                "response",
                "7 · Resposta\n201 confirmado / 409 conflito\nMesma chave recupera resultado",
                410,
                430,
            ),
            node(
                "worker",
                "8 · Depois do commit\nClaim persistido da outbox\nSMTP fora da transação de reserva",
                760,
                680,
            ),
            node(
                "smtp",
                "9 · SMTP aceito\nRetry / lease persistidos\nNão comprova leitura externa",
                1110,
                680,
            ),
        ],
        [
            ("review", "request", "POST", []),
            ("request", "lock", "begin", []),
            ("lock", "validate", "sob lock", []),
            ("validate", "write", "pessoa elegível", []),
            ("write", "integrity", "atomicidade", []),
            ("integrity", "response", "resultado", []),
            ("integrity", "worker", "outbox após commit", []),
            ("worker", "smtp", "at least once", []),
        ],
        "Pools são validados no domínio sob o lock comum. Não existe terceira exclusion constraint para equipamento.",
    ),
    (
        "05-Security-Trust-Boundaries",
        "security-boundaries",
        "Entradas não confiáveis e privilégios separados",
        [
            node(
                "browser",
                "Browser não confiável\nFormulário / URL / payload\nCookie opaco HttpOnly / Secure",
                60,
                180,
            ),
            node(
                "proxy",
                "Fronteira de transporte\nNginx / TLS local\nMesma origem para /api",
                410,
                180,
            ),
            node(
                "identity",
                "Servidor de aplicação\nSessão, CSRF, RBAC e owner\nArgon2id / tokens únicos",
                760,
                180,
            ),
            node("runtime", "Runtime PostgreSQL\nSem superuser / DDL\nAudit sem UPDATE", 1110, 180),
            node(
                "public",
                "Projeção do tutor\nSó seus objetos / resumo público\nSem notas ou motivos internos",
                410,
                470,
            ),
            node(
                "internal",
                "Operação / gestão\nPapel + contexto no servidor\nNotas internas / auditoria",
                760,
                470,
            ),
            node(
                "privileged",
                "Operador offline privilegiado\nMigrations / backup / restore\nCredencial e ferramentas separadas",
                1110,
                470,
            ),
            node(
                "private",
                "Fronteira de artefatos\n.env, contas, chaves e dumps fora do Git\nPreview serve somente docs/case",
                760,
                750,
                610,
                100,
            ),
        ],
        [
            ("browser", "proxy", "HTTPS", []),
            ("proxy", "identity", "validar entrada", []),
            ("identity", "runtime", "privilégio mínimo", []),
            ("identity", "internal", "autorização contextual", []),
            ("identity", "public", "projeção filtrada", [(690, 245), (690, 390), (540, 390)]),
            ("privileged", "runtime", "DDL / recovery", []),
            ("privileged", "private", "custódia local", []),
        ],
        "Menus não são controles de segurança. SMTP aceito não é entrega externa. TLS/backup não cobrem perda do host.",
    ),
    (
        "06-Data-Flow",
        "data-flow",
        "Dados operacionais, projeções e comunicação",
        [
            node(
                "forms",
                "Entradas autenticadas\nContato / pet / serviço / horário\nContratos OpenAPI tipados",
                60,
                180,
            ),
            node(
                "domain",
                "Casos de uso / domínio\nPropriedade e regras\nTransação por mutação",
                410,
                180,
            ),
            node(
                "records",
                "PostgreSQL\nEstado + snapshot contratado\nNotas / eventos / auditoria",
                760,
                180,
            ),
            node(
                "outbox",
                "Outbox privada\nDestinatário / corpo / prazo\nLease / tentativas / supressão",
                1110,
                180,
            ),
            node(
                "tutor",
                "Tutor\nSeus pets / reservas / resumo\nEstado local da comunicação",
                60,
                520,
            ),
            node(
                "staff",
                "Equipe\nAgenda / alerta de perfil\nÚltimos três cuidados anteriores",
                410,
                520,
            ),
            node(
                "metrics",
                "Gestão agregada\nCoorte: início previsto\nEstado atual / responsável final",
                760,
                520,
            ),
            node(
                "smtp",
                "SMTP / Mailpit\nEnvio fora da transação\nSem recibo de leitura externa",
                1110,
                520,
            ),
            node(
                "backup",
                "Backup offline autenticado\nTodas as tabelas + ACLs + GiST → banco novo reconciliado\nArchive e chave separados no mesmo host; não é projeção pública",
                410,
                790,
                610,
                100,
            ),
        ],
        [
            ("forms", "domain", "validar", []),
            ("domain", "records", "persistir junto", []),
            ("records", "outbox", "mesmo commit", []),
            ("outbox", "smtp", "claim / retry", []),
            ("records", "metrics", "SQL agregado", []),
            ("records", "staff", "contexto interno", [(690, 245), (690, 400), (540, 400)]),
            ("records", "tutor", "owner / público", [(750, 325), (190, 325)]),
            (
                "records",
                "backup",
                "banco completo, offline",
                [(1050, 245), (1050, 750), (715, 750)],
            ),
        ],
        "Concluídos usam responsável final; não há divisão de esforço. Indicadores não são receita nem ranking.",
    ),
    (
        "07-Deployment-Staging",
        "deployment",
        "CURRENT · máquina local / sem alta disponibilidade",
        [
            node("user", "Navegador local\nCA de teste\nhttps://localhost:8443", 60, 180),
            node("web", "petland7 / web\nNginx + React estático\nNão root / read-only", 410, 180),
            node(
                "api", "petland7 / api\n2 workers + outbox threads\nSem porta publicada", 760, 180
            ),
            node(
                "pg",
                "petland7 / postgres\nPostgreSQL 17 single-node\nVolume persistente / TLS",
                1110,
                180,
            ),
            node("mail", "petland7 / mailpit\nSTARTTLS\nUI loopback :8026", 760, 480),
            node(
                "job", "petland7 / migrate\nJob separado antes da API\nAlembic head 0007", 1110, 480
            ),
            node(
                "host",
                "Host / ferramentas offline\nBackup local / chave separada\nRestore + reconciliação + ativação",
                410,
                480,
            ),
            node(
                "other",
                "Ambientes independentes\npetland3: dev Vite / outro volume; testes PG efêmeros\npetlanddocs: captura temporária sintética / imagem funcional 2549523",
                60,
                790,
                650,
                100,
            ),
            node(
                "future",
                "POSSIBLE PRODUCTION EVOLUTION\nNão implementada: provedor, Multi-AZ, PITR, SMTP externo, off-host\nSLO/RPO/RTO, observabilidade e balanceamento dependem de D10",
                760,
                790,
                610,
                100,
            ),
        ],
        [
            ("user", "web", "HTTPS local", []),
            ("web", "api", "/api", []),
            ("api", "pg", "verify-full", []),
            ("api", "mail", "STARTTLS", []),
            ("job", "pg", "migrator / DDL", []),
            ("host", "pg", "dump / restore", [(690, 545), (690, 365), (1240, 365)]),
        ],
        "Rede privada entre containers; portas públicas somente loopback. Archive local não cobre perda da máquina.",
    ),
]


def route(source, target, waypoints):
    _, _, x, y, width, height = source
    _, _, tx, ty, tw, th = target
    if waypoints:

        def boundary(cx, cy, w, h, px, py):
            dx, dy = px - cx, py - cy
            factor = min(
                w / 2 / abs(dx) if dx else float("inf"), h / 2 / abs(dy) if dy else float("inf")
            )
            return round(cx + dx * factor, 2), round(cy + dy * factor, 2)

        return [
            boundary(x + width / 2, y + height / 2, width, height, *waypoints[0]),
            *waypoints,
            boundary(tx + tw / 2, ty + th / 2, tw, th, *waypoints[-1]),
        ]
    if abs(tx - x) > abs(ty - y):
        sign = 1 if tx > x else -1
        a = (x + (width if sign > 0 else 0), y + height / 2)
        b = (tx + (0 if sign > 0 else tw), ty + th / 2)
        middle = (a[0] + b[0]) / 2
        return [a, (middle, a[1]), (middle, b[1]), b]
    a = (x + width / 2, y + (height if ty > y else 0))
    b = (tx + tw / 2, ty + (0 if ty > y else th))
    middle = (a[1] + b[1]) / 2
    return [a, (a[0], middle), (b[0], middle), b]


def render():
    mxfile = ET.Element(
        "mxfile", {"host": "app.diagrams.net", "type": "device", "version": "24.7.17"}
    )
    outputs = {}
    markdown = [
        "# Diagramas atuais — PetLand 3.0",
        "",
        f"Referência funcional: `{REFERENCE}`.",
        "",
        "Draw.io editável e SVG/Mermaid compartilham o modelo em [render_architecture.py](../../../scripts/render_architecture.py).",
        "Coordenadas, labels, nós e relações são determinísticos; não é exportação via serviço externo.",
        "",
        "`python scripts/render_architecture.py` regenera; `python scripts/render_architecture.py --check` detecta divergência.",
        "Editar o modelo e regenerar preserva coerência. Edições manuais no Draw.io continuam editáveis, mas não são importadas pelo gerador.",
        "Os diagramas L1–L3 são aproximações C4, não certificação formal. Setas de containers são comunicação; módulos indicam contratos públicos.",
        "",
        "[Abrir arquivo com sete páginas](PetLand_3.0_Architecture.drawio)",
        "",
    ]
    for name, slug, subtitle, nodes, edges, note in PAGES:
        diagram = ET.SubElement(mxfile, "diagram", {"id": slug, "name": name})
        model = ET.SubElement(
            diagram,
            "mxGraphModel",
            {
                "dx": "1440",
                "dy": "1000",
                "grid": "1",
                "gridSize": "10",
                "page": "1",
                "pageWidth": "1440",
                "pageHeight": "1000",
            },
        )
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        header = node(
            "header", f"PETLAND 3.0 · {name}\n{subtitle}\nCURRENT / {REFERENCE}", 60, 30, 1320, 110
        )
        footer = node("footer", note, 60, 935, 1320, 45)
        svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1000" viewBox="0 0 1440 1000" role="img">',
            f"<title>{html.escape(name)}</title><desc>{html.escape(subtitle + '. ' + note)}</desc>",
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#1f5d50"/></marker></defs>',
            '<rect width="1440" height="1000" fill="#f7f5ef"/>',
        ]
        for key, label, x, y, width, height in [header, *nodes, footer]:
            plain = key in {"header", "footer"}
            style = (
                "text;html=0;align=left;fontSize=18;fontColor=#243a35;whiteSpace=wrap;"
                if plain
                else "rounded=1;whiteSpace=wrap;html=0;fillColor=#ffffff;strokeColor=#1f5d50;fontColor=#243a35;fontSize=17;spacing=16;"
            )
            cell = ET.SubElement(
                root,
                "mxCell",
                {"id": key, "value": label, "style": style, "vertex": "1", "parent": "1"},
            )
            ET.SubElement(
                cell,
                "mxGeometry",
                {
                    "x": str(x),
                    "y": str(y),
                    "width": str(width),
                    "height": str(height),
                    "as": "geometry",
                },
            )
            if not plain:
                svg.append(
                    f'<rect id="node-{key}" x="{x}" y="{y}" width="{width}" height="{height}" rx="12" fill="#fff" stroke="#1f5d50" stroke-width="2"/>'
                )
            font_size = 15
            if plain:
                lines = [(line, i == 0) for i, line in enumerate(label.splitlines())]
                line_height = 25
                base = y + 27
            else:
                while True:
                    limit = int((width - 36) / (font_size * 0.60))
                    lines = [
                        (part, i == 0)
                        for i, line in enumerate(label.splitlines())
                        for part in textwrap.wrap(line, width=limit, break_long_words=False)
                    ]
                    line_height = font_size * 1.35
                    if len(lines) * line_height + 24 <= height or font_size <= 12:
                        break
                    font_size -= 1
                base = y + (height - len(lines) * line_height) / 2 + font_size
            for i, (line, bold) in enumerate(lines):
                size = (
                    23
                    if key == "header" and i == 0
                    else 16
                    if key == "footer"
                    else 17
                    if plain
                    else font_size
                )
                weight = "700" if bold else "400"
                svg.append(
                    f'<text data-node="{key}" x="{x + (0 if plain else 18)}" y="{base + i * line_height}" fill="#243a35" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}">{html.escape(line)}</text>'
                )
        by_id = {n[0]: n for n in nodes}
        for i, (source, target, label, points) in enumerate(edges):
            resolved = route(by_id[source], by_id[target], points)
            cell = ET.SubElement(
                root,
                "mxCell",
                {
                    "id": f"edge-{i}",
                    "value": label,
                    "source": source,
                    "target": target,
                    "edge": "1",
                    "parent": "1",
                    "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;strokeColor=#1f5d50;fontColor=#243a35;fontSize=13;labelBackgroundColor=#f7f5ef;",
                },
            )
            geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            array = ET.SubElement(geom, "Array", {"as": "points"})
            for px, py in resolved[1:-1]:
                ET.SubElement(array, "mxPoint", {"x": str(px), "y": str(py)})
            coords = " ".join(f"{px},{py}" for px, py in resolved)
            svg.append(
                f'<polyline points="{coords}" fill="none" stroke="#1f5d50" stroke-width="2" marker-end="url(#arrow)"/>'
            )
            longest = max(
                zip(resolved, resolved[1:], strict=False),
                key=lambda p: abs(p[1][0] - p[0][0]) + abs(p[1][1] - p[0][1]),
            )
            lx, ly = (longest[0][0] + longest[1][0]) / 2, (longest[0][1] + longest[1][1]) / 2 - 9
            # Opaque text stroke keeps labels legible when another connector crosses.
            span = abs(longest[1][0] - longest[0][0])
            limit = max(10, int(min(210, span - 10) / 7)) if span else 28
            parts = textwrap.wrap(label, width=limit, break_long_words=False)
            for j, part in enumerate(parts):
                svg.append(
                    f'<text x="{lx}" y="{ly - (len(parts) - 1 - j) * 15}" text-anchor="middle" fill="#243a35" stroke="#f7f5ef" stroke-width="5" paint-order="stroke" font-family="Arial, sans-serif" font-size="12">{html.escape(part)}</text>'
                )
        svg.append("</svg>")
        outputs[f"{slug}.svg"] = ("\n".join(svg) + "\n").encode()
        markdown += [
            f"## {name}",
            "",
            subtitle,
            "",
            f"![{subtitle}]({slug}.svg)",
            "",
            "```mermaid",
            "flowchart LR",
        ]
        for key, label, *_ in nodes:
            markdown.append(f'  {key}["{label.replace(chr(10), " · ")}"]')
        for source, target, label, _ in edges:
            markdown.append(f'  {source} -->|"{label}"| {target}')
        markdown += ["```", "", note, ""]
    ET.indent(mxfile)
    outputs["PetLand_3.0_Architecture.drawio"] = (
        ET.tostring(mxfile, encoding="utf-8", xml_declaration=True) + b"\n"
    )
    outputs["README.md"] = ("\n".join(markdown).rstrip() + "\n").encode()
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render()
    if args.check:
        different = [
            name
            for name, data in outputs.items()
            if not (DEST / name).is_file() or (DEST / name).read_bytes() != data
        ]
        if different:
            raise SystemExit("Diagram exports differ: " + ", ".join(different))
        print("Seven Draw.io pages, seven SVGs and Mermaid match the current source model.")
    else:
        DEST.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            (DEST / name).write_bytes(data)
        print("Architecture exports regenerated deterministically.")


if __name__ == "__main__":
    main()
