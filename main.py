import os
import random
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from widgets.constants import APP_FOLDER, DRUGS_REGISTRY, SITUATIONS_REGISTRY
from widgets.helpers import ensure_file, read_current_drugs
from widgets.screens import (
    ChooseDrugQuiz,
    DrugQuiz,
    RegisterDrugs,
    RegisterSituation,
    SituationQuiz,
    StartMenu,
)

os.makedirs(APP_FOLDER, exist_ok=True)
ensure_file(DRUGS_REGISTRY, {})
ensure_file(SITUATIONS_REGISTRY, [])


class AnswerWindow(QWidget):
    def __init__(self, message):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel(message)
        self.layout.addWidget(self.label)
        self.button = QPushButton("OK")
        self.button.clicked.connect(self.close)
        self.layout.addWidget(self.button)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.start_screen()

    def _draw_screen(self, layout, buttons=None):
        buttons = buttons or []
        widget = QWidget()
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)

        for button in buttons:
            statusBar.addWidget(button)
        statusBar.show()

    def start_screen(self):
        self.start_widget = StartMenu()
        self.connect_start_screen_buttons()
        self._draw_screen(self.start_widget)

    def connect_start_screen_buttons(self):
        self.start_widget.register_drug.clicked.connect(self.draw_register_drug_screen)
        self.start_widget.register_situation.clicked.connect(self.draw_register_situation_screen)
        self.start_widget.situation_quiz.clicked.connect(self.draw_situation_quiz_screen)
        self.start_widget.random_quiz.clicked.connect(self.random_quiz)
        self.start_widget.choice_quiz.clicked.connect(self.draw_choose_quiz_screen)

    def draw_register_drug_screen(self):
        self.register_drug_widget = RegisterDrugs()
        self.register_drug_widget.cancel_button.clicked.connect(self.start_screen)
        self.register_drug_widget.save_button.clicked.connect(lambda: self.save_content(self.register_drug_widget))
        buttons = [
            self.register_drug_widget.cancel_button,
            self.register_drug_widget.save_button,
            self.register_drug_widget.add_new_line_button,
        ]
        self._draw_screen(self.register_drug_widget, buttons)

    def draw_register_situation_screen(self):
        self.register_situation_widget = RegisterSituation()
        self.register_situation_widget.cancel_button.clicked.connect(self.start_screen)
        self.register_situation_widget.save_button.clicked.connect(
            lambda: self.save_content(self.register_situation_widget)
        )
        buttons = [
            self.register_situation_widget.cancel_button,
            self.register_situation_widget.save_button,
            self.register_situation_widget.add_new_line_button,
        ]

        self._draw_screen(self.register_situation_widget, buttons)

    def draw_situation_quiz_screen(self):
        self.situation_quiz_widget = SituationQuiz()
        self.situation_quiz_widget.cancel_button.clicked.connect(self.start_screen)
        buttons = [self.situation_quiz_widget.cancel_button]
        if hasattr(self.situation_quiz_widget, "answer_button"):
            self.situation_quiz_widget.answer_button.clicked.connect(
                lambda: self.check_situation_answer(self.situation_quiz_widget)
            )
            buttons.append(self.situation_quiz_widget.answer_button)
        self._draw_screen(self.situation_quiz_widget, buttons)

    def draw_choose_quiz_screen(self):
        self.choose_drug_widget = ChooseDrugQuiz()
        self.choose_drug_widget.cancel_button.clicked.connect(self.start_screen)
        buttons = [self.choose_drug_widget.cancel_button]
        if hasattr(self.choose_drug_widget, "start_button"):
            self.choose_drug_widget.start_button.clicked.connect(
                lambda: self.draw_quiz_screen(
                    self.choose_drug_widget.combo_options.currentText(),
                    quiz_type="choose"
                )
            )
            buttons.append(self.choose_drug_widget.answer_button)
        
        self._draw_screen(self.choose_drug_widget, buttons)

    def draw_quiz_screen(self, drug, quiz_type):
        quiz_widget = DrugQuiz(drug, quiz_type)
        quiz_widget.cancel_button.clicked.connect(self.start_screen)
        quiz_widget.answer_button.clicked.connect(lambda: self.check_drug_answer(quiz_widget))
        buttons = [quiz_widget.cancel_button, quiz_widget.answer_button]
        self._draw_screen(quiz_widget, buttons)

    def save_content(self, widget):
        widget.save()
        self.start_screen()

    def random_quiz(self):
        current_content = read_current_drugs()
        if not current_content:
            self.answer_window = AnswerWindow("No substances registered. Please register some substances first.")
            self.answer_window.show()
            return
        random_item = random.choice(list(current_content.keys()))
        self.draw_quiz_screen(random_item, "random")

    def check_drug_answer(self, widget):
        widget.answer()
        next_button = QPushButton("Next question")
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.start_screen)
        if widget.quiz_type == "random":
            next_button.clicked.connect(self.random_quiz)
        else:
            next_button.clicked.connect(lambda: self.draw_quiz_screen(widget.drug, widget.quiz_type))
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        statusBar.addWidget(next_button)
        statusBar.addWidget(cancel_button)
        statusBar.show()

    def check_situation_answer(self, widget):
        widget.answer()
        next_button = QPushButton("Next question")
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.start_screen)
        next_button.clicked.connect(self.draw_situation_quiz_screen)
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        statusBar.addWidget(next_button)
        statusBar.addWidget(cancel_button)
        statusBar.show()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
