class ErroErp(Exception):
    """Falha na integração com o ERP. A mensagem é técnica (vai para o log e para ultimo_erro)."""


class ErpTempoEsgotado(ErroErp):
    pass


class ErpErroServico(ErroErp):
    pass


class ErpRespostaInvalida(ErroErp):
    pass
