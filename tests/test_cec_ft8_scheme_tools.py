from sat_bridge.cec_ft8_scheme_tools import infer_judgement, render_cec_ft8_scheme_markdown


def test_infer_judgement_prefers_digimanager_timing_fix() -> None:
    report = {
        "timing_summary": {"comparison": {"same_payload_shape": False}, "diagnosis": {"likely_timing_owner": "still_unclear"}},
        "digimanager_summary": {"applied_patches": [{"name": "udpdatacheck_ft4_forward_gate"}]},
        "public_fsk_reference": {
            "aircopy_uses_sendfskdata": True,
            "aircopy_packet_words": 36,
            "aircopy_reg72_baud_1200": True,
            "radio_supports_baseband_modes": True,
        },
    }
    judgement = infer_judgement(report)
    assert judgement["public_bk4819_packet_fsk_fit_for_ft4"] == "unlikely"
    assert judgement["current_best_direction"] == "treat_digimanager_sender_timing_as_primary_ft4_fix_target"
    assert judgement["ft4_gate_open_via_digimanager_patch"] is True


def test_render_markdown_mentions_capstone_judgement() -> None:
    report = {
        "judgement": {
            "likely_author_ft8_tx_scheme": "custom_digital_sender_chain_plus_clean_baseband_or_custom_cec_tx",
            "public_bk4819_packet_fsk_fit_for_ft4": "unlikely",
            "current_best_direction": "treat_digimanager_sender_timing_as_primary_ft4_fix_target",
            "confidence": "medium",
            "summary_lines": ["line a", "line b"],
            "recommended_next_step": "next step",
        },
        "firmware": {"embedded_version": "*KD8CEC_FROM_SOU"},
        "public_fsk_reference": {
            "aircopy_uses_sendfskdata": True,
            "aircopy_packet_words": 36,
            "aircopy_reg72_baud_1200": True,
            "aircopy_reg58_fsk_enable": True,
            "aircopy_reg5d_length_72_bytes": True,
        },
        "ft4_primary_sources": [{"title": "FT4 and FT8 Communication Protocols", "url": "https://wsjt.sourceforge.io/FT4_FT8_QEX.pdf"}],
    }
    text = render_cec_ft8_scheme_markdown(report)
    assert "BK4819 公开 packet FSK 硬件链是否适合直接做 FT4" in text
    assert "当前最应该优先修的方向" in text
    assert "FT4 and FT8 Communication Protocols" in text
