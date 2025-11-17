from __future__ import annotations

from typing import Final

INTERFACE_THEME_CSS: Final = """
        .adsorfit-card {
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.45);
            box-shadow: 0 22px 60px -40px rgba(30, 41, 59, 0.45);
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        }

        .adsorfit-card.dark {
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
            border-color: rgba(148, 163, 184, 0.35);
        }

        .adsorfit-heading {
            color: #0f172a;
            letter-spacing: 0.015em;
        }

        .adsorfit-heading.dark {
            color: #e2e8f0;
        }

        .adsorfit-status {
            font-family: "JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular,
                SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
                monospace;
            background-color: rgba(15, 23, 42, 0.04);
            border-radius: 12px;
            padding: 1rem;
            width: 100%;
            display: block;
            box-sizing: border-box;
            align-self: stretch;
        }

        .q-textarea__native {
            font-family: "JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular,
                SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
                monospace;
        }
        """


CARD_BASE_CLASSES: Final = (
    "adsorfit-card w-full h-full rounded-2xl border border-slate-200/70 "
    "bg-white/95 shadow-xl shadow-slate-900/5 dark:adsorfit-card "
    "dark:border-slate-700/80"
)


PAGE_CONTAINER_CLASSES: Final = (
    "adsorfit-page-container w-full max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6"
)
