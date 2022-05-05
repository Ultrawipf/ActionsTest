from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QWidget,QGroupBox
from PyQt6.QtWidgets import QMessageBox,QVBoxLayout,QCheckBox,QButtonGroup,QPushButton,QLabel,QSpinBox,QComboBox
from PyQt6 import uic
import main
from helper import res_path,classlistToIds
from optionsdialog import OptionsDialog,OptionsDialogGroupBox
from base_ui import CommunicationHandler
import portconf_ui

class AnalogOptionsDialog(OptionsDialog):
    def __init__(self,name,id, main):
        self.main = main
        self.dialog = OptionsDialogGroupBox(name,main)

        if(id == 0): # local analog
            self.dialog = (AnalogInputConf(name,self.main))
        if(id == 1): # can analog
            self.dialog = (CANAnalogConf(name,self.main))

        OptionsDialog.__init__(self, self.dialog,main)


class AnalogInputConf(OptionsDialogGroupBox,CommunicationHandler):
    analogbtns = QButtonGroup()
    axes = 0
    def __init__(self,name,main):
        self.main = main
        OptionsDialogGroupBox.__init__(self,name,main)
        CommunicationHandler.__init__(self)
        self.analogbtns.setExclusive(False)
        self.buttonBox = QGroupBox("Pins")
        self.buttonBoxLayout = QVBoxLayout()
        self.buttonBox.setLayout(self.buttonBoxLayout)

    def initUI(self):
        layout = QVBoxLayout()
        self.autorangeBox = QCheckBox("Autorange")
        layout.addWidget(self.autorangeBox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
    def readValues(self):
        self.getValueAsync("apin","pins",self.createAinButtons,0,conversion=int)
        self.getValueAsync("apin","autocal",self.autorangeBox.setChecked,0,conversion=int)
        

    def createAinButtons(self,axes):
        self.axes = axes
        # remove buttons
        for i in range(self.buttonBoxLayout.count()):
            b = self.buttonBoxLayout.takeAt(0)
            self.buttonBoxLayout.removeItem(b)
            b.widget().deleteLater()
        for b in self.analogbtns.buttons():
            self.analogbtns.removeButton(b)

        # add buttons
        for i in range(axes):
            btn=QCheckBox(str(i+1),self)
            self.analogbtns.addButton(btn,i)
            self.buttonBoxLayout.addWidget(btn)

        def f(axismask):
            for i in range(self.axes):
                self.analogbtns.button(i).setChecked(axismask & (1 << i))
        self.getValueAsync("apin","mask",f,0,conversion=int)

    def apply(self):
        mask = 0
        for i in range(self.axes):
            if (self.analogbtns.button(i).isChecked()):
                mask |= 1 << i

        self.sendValue("apin","mask",mask)
        self.sendValue("apin","autocal",1 if self.autorangeBox.isChecked() else 0)

    def onclose(self):
        self.removeCallbacks()


class CANAnalogConf(OptionsDialogGroupBox,CommunicationHandler):

    def __init__(self,name,main):
        self.main = main
        OptionsDialogGroupBox.__init__(self,name,main)
        CommunicationHandler.__init__(self)


    def initUI(self):
        vbox = QVBoxLayout()

        self.numAinBox = QSpinBox()
        self.numAinBox.setMinimum(1)
        self.numAinBox.setMaximum(8)
        vbox.addWidget(QLabel("Number of axes"))
        vbox.addWidget(self.numAinBox)
        self.numAinBox.valueChanged.connect(self.amountChanged)

        self.canIdBox = QSpinBox()
        self.canIdBox.setMinimum(1)
        self.canIdBox.setMaximum(0x7ff)
        vbox.addWidget(QLabel("CAN frame ID"))
        vbox.addWidget(self.canIdBox)
        self.canIdBox.valueChanged.connect(self.amountChanged)

        self.infoLabel = QLabel("")
        vbox.addWidget(self.infoLabel)

        self.cansettingsbutton = QPushButton("CAN settings")
        self.canOptions = portconf_ui.CanOptionsDialog(0,"CAN",self.main)
        self.cansettingsbutton.clicked.connect(self.canOptions.exec)
        vbox.addWidget(self.cansettingsbutton)
        
        self.setLayout(vbox)

    def onclose(self):
        self.removeCallbacks()

    def amountChanged(self,_):
        amount = self.numAinBox.value()
        text = ""
        for packet in range(int((amount-1)/4)+1):
            text += f"ID {self.canIdBox.value()+packet}:\n("
            for value in range(4):
                if(value < int(amount - int(packet*4))):
                    text += f"| v{value+1+packet*4}[0:7], v{value+1+packet*4}[8:15] |"
                else:
                    text += "|xx||xx|"
            text += ")\n"

        self.infoLabel.setText(text)

    def apply(self):
        self.sendValue("cananalog","canid",self.canIdBox.value())
        self.sendValue("cananalog","amount",self.numAinBox.value())

    def maximumCb(self,val):
        self.numAinBox.setMaximum(val)
        self.canIdBox.setMaximum(0x7ff - int((val-1)/4))
    
    def readValues(self):
        self.getValueAsync("cananalog","amount",self.numAinBox.setValue,0,conversion=int)
        self.getValueAsync("cananalog","maxamount",self.maximumCb,0,conversion=int)
        self.getValueAsync("cananalog","canid",self.canIdBox.setValue,0,conversion=int)

        
 