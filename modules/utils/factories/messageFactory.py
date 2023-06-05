from Ferramentas_Producao.modules.utils.message.htmlMessageDialog  import HtmlMessageDialog
from Ferramentas_Producao.modules.utils.message.infoMessageBox  import InfoMessageBox
from Ferramentas_Producao.modules.utils.message.errorMessageBox  import ErrorMessageBox
from Ferramentas_Producao.modules.utils.message.questionMessageBox  import QuestionMessageBox
from Ferramentas_Producao.modules.utils.message.ruleMessageDialog  import RuleMessageDialog

class MessageFactory:

    def createMessage(self, messageType):
        messageTypes = {
            'HtmlMessageDialog': HtmlMessageDialog,
            'RuleMessageDialog': RuleMessageDialog,
            'InfoMessageBox': InfoMessageBox,
            'ErrorMessageBox': ErrorMessageBox,
            'QuestionMessageBox': QuestionMessageBox

        }
        return messageTypes[messageType]()