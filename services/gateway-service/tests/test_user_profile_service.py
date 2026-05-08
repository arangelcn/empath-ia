from src.services.user_profile_service import UserProfileService


def test_create_standardized_profile_extracts_profile_signals():
    service = UserProfileService()

    profile = service.create_standardized_profile(
        "toni",
        {
            "idade": "34 anos",
            "genero": "masculino",
            "cor_raca": "pardo",
            "localizacao": "São Paulo, SP",
            "ocupacao": "trabalho em tecnologia",
            "motivacao_terapia": "Quero trabalhar ansiedade e autoestima",
            "relacao_familia": "Tenho apoio família",
            "situacao_moradia": "Moro com família",
            "informacoes_adicionais": "Busco crescimento pessoal",
        },
    )

    assert profile["personal_info"]["idade"]["valor"] == 34
    assert profile["personal_info"]["genero"]["categoria"] == "masculino"
    assert profile["personal_info"]["cor_raca"]["categoria"] == "pardo"
    assert profile["personal_info"]["localizacao"]["cidade"] == "São Paulo"
    assert "Trabalhar questões de ansiedade" in profile["therapeutic_info"]["objetivos_identificados"]
    assert "Fortalecer autoestima" in profile["therapeutic_info"]["objetivos_identificados"]
    assert "ansiedade" in profile["keywords"]
    assert profile["data_source"] == "session-1_registration"
