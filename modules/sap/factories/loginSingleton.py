from Ferramentas_Producao.modules.sap.widgets.login  import Login

class LoginSingleton:

    login = None

    @staticmethod
    def getInstance():
        if not LoginSingleton.login:
            LoginSingleton.login = Login()
        return LoginSingleton.login