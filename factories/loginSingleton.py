from SAP_Operador.widgets.login  import Login

class LoginSingleton:

    login = None

    @staticmethod
    def getInstance(controller):
        if not LoginSingleton.login:
            LoginSingleton.login = Login(controller)
        return LoginSingleton.login