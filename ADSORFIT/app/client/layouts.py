from __future__ import annotations

from typing import Final


INTERFACE_THEME_CSS: Final = """
        .q-table__container {
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 10px 28px -18px rgba(15, 23, 42, 0.25);
        }

        .q-table thead th {
            background-color: #f8fafc;
            color: #1f2937;
            font-weight: 500;
        }

        .q-table tbody td {
            border-bottom: 1px solid #e2e8f0;
        }

        .q-table tbody tr:nth-child(even) td {
            background-color: #f9fafb;
        }

        .q-table tbody tr:last-child td {
            border-bottom: none;
        }
        """


PAGE_CONTAINER_CLASSES: Final = "adsorfit-page-container flex flex-col gap-6"