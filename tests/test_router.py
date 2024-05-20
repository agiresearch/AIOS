from src.router.router import ModelRouter

def test_router():
    router = ModelRouter()

    response = router.evaluate('Calculate the length of a cow while it is grazing in the fields')

    assert isinstance(response, str)