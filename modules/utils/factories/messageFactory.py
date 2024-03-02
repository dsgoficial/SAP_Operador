from SAP_Operador.modules.utils.message.htmlMessageDialog  import HtmlMessageDialog
from SAP_Operador.modules.utils.message.infoMessageBox  import InfoMessageBox
from SAP_Operador.modules.utils.message.errorMessageBox  import ErrorMessageBox
from SAP_Operador.modules.utils.message.questionMessageBox  import QuestionMessageBox
from SAP_Operador.modules.utils.message.ruleMessageDialog  import RuleMessageDialog

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