import sys
import matplotlib
import requests
import numpy as np
from bs4 import BeautifulSoup
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QWidget, QComboBox,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("IMDb vs MAL")
        # MainWindow.setFixedHeight(self, 800)
        # MainWindow.setFixedWidth(self, 1400)

        self.graph_left = MplCanvas(self, width=20, height=20, dpi=100)
        self.graph_right = MplCanvas(self, width=20, height=20, dpi=100)
        self.graph_right.figure.clear()
        self.graph_left.figure.clear()
        self.canvas1 = FigureCanvas(self.graph_left.figure)
        self.canvas2 = FigureCanvas(self.graph_right.figure)

        self.outerLayout = QtWidgets.QVBoxLayout()
        self.topLayout = QtWidgets.QHBoxLayout()

        self.pageCombo = QComboBox()
        self.pageCombo.addItems(["MAL vs IMDb (Anime)", "Anime vs Manga (MAL)"])
        self.pageCombo.adjustSize()
        self.pageCombo.activated.connect(self.update_page)
        self.cur_page = 1
        self.topLayout.addWidget(self.pageCombo)

        self.search = QLineEdit()
        self.topLayout.addWidget(self.search)
        self.search.installEventFilter(self)

        self.graph_layout = QtWidgets.QHBoxLayout()
        self.outerLayout.addLayout(self.topLayout)
        self.outerLayout.addLayout(self.graph_layout)

        self.graph_layout.addWidget(self.canvas1)
        self.graph_layout.addWidget(self.canvas2)
        self.setLayout(self.outerLayout)
        self.setLayout(self.topLayout)
        self.setLayout(self.graph_layout)
        self.show()

    def update_page(self):
        if self.pageCombo.currentText()[0] == "M":
            self.cur_page = 1
        elif self.pageCombo.currentText()[0] == "A":
            self.cur_page = 2
        else:
            print("Error")

    def eventFilter(self, obj, event):
        # code from https://stackoverflow.com/questions/57698744/how-can-i-know-when-the-enter-key-was-pressed-on-qtextedit
        if event.type() == QtCore.QEvent.KeyPress and obj is self.search:
            if event.key() == QtCore.Qt.Key_Return and self.search.hasFocus():
                self.searched(self.search.text())
        return super().eventFilter(obj, event)

    def searched(self, title):
        if self.cur_page == 1:
            self.update_MAL_graph_anime(title)
            self.update_IMDb_graph(title)
        else:
            self.update_MAL_graph_anime(title)
            self.update_MAL_graph_manga(title)
        self.show()

    def update_MAL_graph_anime(self, search):
        ####################### Code from rapidapi.com #######################
        url = "https://jikan1.p.rapidapi.com/search/anime"

        querystring = {"q": search, "page": "1"}

        headers = {
            "X-RapidAPI-Key": "Enter API Key here",
            "X-RapidAPI-Host": "jikan1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        ####################### code from rapidapi.com end #######################

        test = response.text.find("results\":[]")
        if response.text.find("results\":[]") != -1:
            self.graph_left.figure.clear()
            self.canvas1.draw()
        else:

            start_idx = response.text.find("score\":") + 7
            end_idx = response.text.find(",\"start_")
            rating = response.text[start_idx:end_idx]

            # Finds MAL_id

            start_idx = response.text.find("\"mal_id\":") + 9
            end_idx = response.text.find(",\"url\":")
            mal_id = response.text[start_idx:end_idx]

            url = "https://jikan1.p.rapidapi.com/anime/" + mal_id + "/stats"
            response = requests.request("GET", url, headers=headers)
            text = response.text
            ratings = []
            sum = 0

            if text.find("status\":400") != -1:
                print("Error")
                self.graph_left.figure.clear()
                self.canvas1.draw()
            else:

                for i in range(1, 11):
                    start_idx = text.find("votes\":") + 7
                    end_idx = text.find(",\"percentage\":")
                    ratings.append(int(text[start_idx:end_idx]))
                    text = text[end_idx + 14:len(text)]
                    sum += ratings[i - 1]

                x_axis = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                self.graph_left.figure.clear()
                self.graph_left.axes = self.graph_left.figure.add_subplot(111)
                self.graph_left.axes.bar(x_axis, ratings, fc="#a6bbef")
                self.graph_left.axes.set_ylabel("Votes")
                self.graph_left.axes.set_xlabel("Rating")
                if self.cur_page == 1:
                    self.graph_left.axes.set_title("MAL User Ratings")
                else:
                    self.graph_left.axes.set_title("MAL User Ratings: Anime ")

                self.graph_left.axes.set_xticks(np.arange(1, 11, 1))
                self.graph_left.axes.set_ylim(top=max(ratings) * 1.2)

                for idx, votes in enumerate(ratings):
                    percentage = float(ratings[idx]) / sum * 100
                    percentage_s = str(percentage)[0:4]
                    percentage = float(percentage_s)
                    self.graph_left.axes.text(idx + 1, ratings[idx],
                                              str(percentage) + "%" + "\n" + "(" + str(votes) + ")",
                                              ha="center",
                                              va="bottom", fontsize=7)

                self.canvas1.draw()

    def update_MAL_graph_manga(self, search):
        ####################### Code from rapidapi.com #######################

        url = "https://jikan1.p.rapidapi.com/search/manga"

        querystring = {"q": search, "page": "1"}

        headers = {
            "X-RapidAPI-Key": "Enter API Key here",
            "X-RapidAPI-Host": "jikan1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        ####################### code from rapidapi.com end #######################

        test = response.text.find("results\":[]")
        if response.text.find("results\":[]") != -1:
            self.graph_right.figure.clear()
            self.canvas2.draw()
        else:

            start_idx = response.text.find("score\":") + 7
            end_idx = response.text.find(",\"start_")
            rating = response.text[start_idx:end_idx]

            # Finds MAL_id

            start_idx = response.text.find("\"mal_id\":") + 9
            end_idx = response.text.find(",\"url\":")
            mal_id = response.text[start_idx:end_idx]

            url = "https://jikan1.p.rapidapi.com/manga/" + mal_id + "/stats"
            response = requests.request("GET", url, headers=headers)
            text = response.text
            ratings = []
            sum = 0
            if text.find("status\":400") != -1:
                print("Error")
                self.graph_right.figure.clear()
                self.canvas2.draw()
            else:
                for i in range(1, 11):
                    start_idx = text.find("votes\":") + 7
                    end_idx = text.find(",\"percentage\":")
                    ratings.append(int(text[start_idx:end_idx]))
                    text = text[end_idx + 14:len(text)]
                    sum += ratings[i - 1]

                x_axis = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                self.graph_right.figure.clear()
                self.graph_right.axes = self.graph_right.figure.add_subplot(111)
                self.graph_right.axes.bar(x_axis, ratings, fc="#a6bbef")
                self.graph_right.axes.set_ylabel("Votes")
                self.graph_right.axes.set_xlabel("Rating")
                self.graph_right.axes.set_title("MAL User Ratings: Manga")
                self.graph_right.axes.set_xticks(np.arange(1, 11, 1))
                self.graph_right.axes.set_ylim(top=max(ratings) * 1.2)

                for idx, votes in enumerate(ratings):
                    percentage = float(ratings[idx]) / sum * 100
                    percentage_s = str(percentage)[0:4]
                    percentage = float(percentage_s)
                    self.graph_right.axes.text(idx + 1, ratings[idx],
                                               str(percentage) + "%" + "\n" + "(" + str(votes) + ")",
                                               ha="center",
                                               va="bottom", fontsize=7)

                self.canvas2.draw()

    def update_IMDb_graph(self, search):
        # Looks through search results page to find the id of the anime searched
        # With this id we can go to the anime page and find the ratings
        anime_search_url = 'https://www.imdb.com/find?q=' + search
        response = requests.get(anime_search_url)
        soup = BeautifulSoup(response.text, "html.parser")
        header = soup.find("h1", {"class": "findHeader"})
        if header.text[0] != "N":

            title = soup.find("td", {"class": "result_text"})
            link = title.contents[1].attrs['href']
            start_idx = link.find("tt")
            end_idx = link.find('/"')
            id = link[start_idx:end_idx]

            anime_page_url = "https://www.imdb.com/title/" + id
            response = requests.get(anime_page_url)
            soup = BeautifulSoup(response.text, "html.parser")
            rating = soup.find("span", {"class": "sc-7ab21ed2-1 jGRxWM"})
            if rating is not None:

                rating = rating.text

                anime_ratings_page_url = "https://www.imdb.com/title/" + id + "/ratings"
                response = requests.get(anime_ratings_page_url)
                soup = BeautifulSoup(response.text, "html.parser")
                rating_votes_text = soup.find_all("div", {"class": "leftAligned"})
                rating_votes_text = rating_votes_text[1:11]
                rating_votes_text.reverse()
                rating_votes_s = []
                sum = 0
                for i in range(len(rating_votes_text)):
                    rating_votes_s.append(rating_votes_text[i].text)
                    rating_votes_s[i] = rating_votes_s[i].replace(',', '')

                rating_votes = []
                for i in range(len(rating_votes_s)):
                    rating_votes.append(int(rating_votes_s[i]))
                    sum += rating_votes[i]

                x_axis = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                self.graph_right.figure.clear()
                self.graph_right.axes = self.graph_right.figure.add_subplot(111)

                self.graph_right.axes.bar(x_axis, rating_votes, fc="#E6B91E")
                self.graph_right.axes.set_ylabel("Votes")
                self.graph_right.axes.set_xlabel("Rating")
                self.graph_right.axes.set_title("IMDb User Ratings ")
                self.graph_right.axes.set_xticks(np.arange(1, 11, 1))
                self.graph_right.axes.set_ylim(top=max(rating_votes) * 1.2)

                for idx, votes in enumerate(rating_votes):
                    percentage = float(rating_votes[idx]) / sum * 100
                    percentage_s = str(percentage)[0:4]
                    percentage = float(percentage_s)
                    self.graph_right.axes.text(idx + 1, rating_votes[idx],
                                               str(percentage) + "%" + "\n" + "(" + str(rating_votes[idx]) + ")",
                                               ha="center", va="bottom", fontsize=7)

                self.canvas2.draw()
            else:
                self.graph_right.figure.clear()
                self.canvas2.draw()
        else:
            self.graph_right.figure.clear()
            self.canvas2.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

