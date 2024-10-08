import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup as bs4
import pandas as pd
from urllib.parse import quote
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager
import matplotlib.pyplot as plt
import webbrowser

class JobMatcher:
    def __init__(self, root):
        self.skills_pair = {}
        self.skills_list = []
        self.df = pd.DataFrame()
        self.selected_skills = []

        self.root = root
        self.root.title("104 Job Skills Analyzer")

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text="請輸入關鍵字：").grid(row=0, column=0, sticky=tk.E)
        self.keyword_entry = ttk.Entry(self.root)
        self.keyword_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky=tk.W)

        ttk.Label(self.root, text="請輸入要搜尋的總頁數：").grid(row=1, column=0, sticky=tk.E)
        self.page_entry = ttk.Entry(self.root)
        self.page_entry.grid(row=1, column=1, padx=(0, 10), pady=5, sticky=tk.W)

        ttk.Label(self.root, text="請選擇要查詢的年資：").grid(row=2, column=0, sticky=tk.E)
        self.exp_var = tk.StringVar()
        self.exp_combobox = ttk.Combobox(self.root, textvariable=self.exp_var, values=["不選擇","一年以下", "一至三年", "三至五年", "五至十年", "十年以上"])
        self.exp_combobox.grid(row=2, column=1, padx=(0, 10), pady=5, sticky=tk.W)
        self.exp_combobox.current(0)

        ttk.Button(self.root, text="搜尋", command=self.start_search).grid(row=3, columnspan=2, pady=10)

        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        ttk.Label(self.root, text="請勾選你的技能").grid(row=5, column=0, sticky=tk.E)
        self.result_frame = ttk.Frame(self.root)
        self.result_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

        self.canvas = tk.Canvas(self.result_frame)
        self.scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        ttk.Button(self.root, text="匹配工作", command=self.match_skills).grid(row=7, columnspan=2, pady=10)

    def start_search(self):
        threading.Thread(target=self.search_jobs).start()

    def search_jobs(self):
        self.keyword = self.keyword_entry.get()
        self.page = int(self.page_entry.get())
        self.exp = self.exp_var.get()
        exp_dict = {
            "不選擇": "0",
            "一年以下": "1",
            "一至三年": "3",
            "三至五年": "5",
            "五至十年": "10",
            "十年以上": "99"
        }
        self.exp = exp_dict.get(self.exp, "99")
        self.encoded_keyword = quote(self.keyword)
        self.rewrite_url()
        joblist = self.joblist_url()
        self.getinfo(joblist)
        self.analyze()

    def rewrite_url(self):
        if self.exp == "0":
            base_url = ('https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&'
                        'expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=12&asc=0&page={}&'
                        'mode=s&jobsource=index_s&langFlag=0&langStatus=0&recommendJob=1&hotJob=1')
            self.url = base_url.format(self.encoded_keyword, '{}')
        else:
            base_url = ('https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&'
                        'expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=12&asc=0&page={}&'
                        'jobexp={}&mode=s&jobsource=index_s&langFlag=0&langStatus=0&recommendJob=1&hotJob=1')
            self.url = base_url.format(self.encoded_keyword, '{}', self.exp)

    def joblist_url(self):
        joblist = []
        for page_num in range(1, self.page + 1):
            current_url = self.url.format(page_num)
            job_list = requests.get(current_url)
            soup = bs4(job_list.text, 'lxml')

            job_blocks = soup.find_all('div', class_='b-block__left')
            if not job_blocks:
                break

            for job_block in job_blocks:
                jobs = job_block.find_all('a', class_='js-job-link')
                for job in jobs:
                    href = job.get('href')
                    if href:
                        joblist.append(href.lstrip('//'))
            self.root.after(0, self.progress.step, 100 / self.page)
        return joblist

    def getinfo(self, joblist):
        for work_url in joblist:
            if not work_url.startswith('http'):
                work_url = 'https://' + work_url

            work = requests.get(work_url)
            soup = bs4(work.text, 'lxml')

            temp_list = []
            skill_blocks = soup.find_all('a', class_='tools text-gray-deep-dark d-inline-block')
            for skill_block in skill_blocks:
                u_tag = skill_block.find('u')
                if u_tag:
                    skill = u_tag.text.strip()
                    temp_list.append(skill)

            self.skills_pair[work_url] = temp_list
            self.skills_list.extend(temp_list)
            self.root.after(0, self.progress.step, 100 / len(joblist))

    def analyze(self):
        skill_counts = pd.Series(self.skills_list).value_counts()
        self.df = pd.DataFrame(skill_counts).reset_index()
        self.df.columns = ['技能', '次數']
        self.df = self.df.sort_values(by='次數', ascending=False)
        self.display_results()
        self.display_statistics()
        self.display_bar_plot()

    def display_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        skills = self.df['技能'].tolist()
        self.skill_vars = []

        for i, skill in enumerate(skills):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.scrollable_frame, text=skill, variable=var)
            chk.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=5)
            self.skill_vars.append((skill, var))

    def display_statistics(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("技能統計表")

        stats_text = tk.Text(stats_window, height=20, width=50)
        stats_text.pack()

        stats_text.insert(tk.END, self.df.to_string(index=False))

    def display_bar_plot(self):
        plot_window = tk.Toplevel(self.root)
        plot_window.title("技能統計柱狀圖")

        fig = Figure(figsize=(8, 6), dpi=100)
        self.df = self.df.head(10)  
        ax = fig.add_subplot(111)
        ax.bar(self.df['技能'], self.df['次數'])
        ax.set_xlabel('skill', fontsize=12)
        ax.set_ylabel('count', fontsize=12)
        ax.set_title('Top ten skills plot', fontsize=14)

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def match_skills(self):
        selected_skills = [skill for skill, var in self.skill_vars if var.get()]
        selected_skill_set = set(selected_skills)

        matching_urls = []
        for url, skill_list in self.skills_pair.items():
            skill_set = set(skill_list)
            if skill_set.issubset(selected_skill_set):
                matching_urls.append(url)

        if matching_urls:
            self.show_results(matching_urls, selected_skills)
        else:
            messagebox.showinfo("匹配結果", "沒有找到符合條件的工作。")

    def shorten_url(self, url, max_length=50):
        if len(url) > max_length:
            return url[:max_length] + '...'
        return url

    def show_results(self, urls, selected_skills):
        result_window = tk.Toplevel(self.root)
        result_window.title("您適合以下的工作")

        result_frame = ttk.Frame(result_window)
        result_frame.pack(fill="both", expand=True)

        columns = ("url",)
        tree = ttk.Treeview(result_frame, columns=columns, show="headings")
        tree.heading("url", text="工作超連結")
        tree.pack(fill="both", expand=True)

        for url in urls:
            shortened_url = self.shorten_url(url)
            tree.insert("", "end", values=(shortened_url,))

        tree.bind("<Double-1>", self.open_url)

    def open_url(self, event):
        item = event.widget.selection()
        if item:
            url = event.widget.item(item, "values")[0]
            webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    app = JobMatcher(root)
    root.mainloop()
