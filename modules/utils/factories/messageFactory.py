from Ferramentas_Producao.modules.utils.message.htmlMessageDialog  import HtmlMessageDialog
from Ferramentas_Producao.modules.utils.message.infoMessageBox  import InfoMessageBox
from Ferramentas_Producao.modules.utils.message.errorMessageBox  import ErrorMessageBox
from Ferramentas_Producao.modules.utils.message.questionMessageBox  import QuestionMessageBox

class MessageFactory:

    def createHTMLMessageDialog(self):
        return HtmlMessageDialog()

    def createInfoMessageBox(self):
        return InfoMessageBox()

    def createErrorMessageBox(self):
        return ErrorMessageBox()

    def createQuestionMessageBox(self):
        return QuestionMessageBox()