#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline package -- Re-exports all public names for backward compatibility."""

from pipeline.helpers import (  # noqa: F401
    _print,
    resolve_scan_root,
    list_rpy_files,
    score_file,
    pick_pilot_files,
    copy_subset_to_input,
    run_main,
    package_output,
    _normalize_ws,
)

from pipeline.gate import (  # noqa: F401
    evaluate_gate,
    collect_files_with_untranslated,
    collect_strings_stats,
    attribute_untranslated,
    write_report_summary_md,
)

from pipeline.stages import (  # noqa: F401
    _run_retranslate_phase,
    _run_tl_mode_phase,
    _run_pilot_phase,
    _run_full_translation_phase,
    _run_final_report,
)
