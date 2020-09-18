from Ferramentas_Producao.modules.utils.message.htmlMessageDialog  import HtmlMessageDialog
from Ferramentas_Producao.modules.utils.message.infoMessageBox  import InfoMessageBox
from Ferramentas_Producao.modules.utils.message.errorMessageBox  import ErrorMessageBox
from Ferramentas_Producao.modules.utils.message.questionMessageBox  import QuestionMessageBox

class MessageFactory:

    def createMessage(self, messageType):
        messageTypes = {
            'HtmlMessageDialog': HtmlMessageDialog,
            'InfoMessageBox': InfoMessageBox,
            'ErrorMessageBox': ErrorMessageBox,
            'QuestionMessageBox': QuestionMessageBox

        }
        return messageTypes[messageType]()