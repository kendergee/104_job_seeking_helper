import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup as bs4
import pandas as pd
from urllib.parse import quote
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager
import matplotlib.pyplot as plt
import matplotlib

zh_font = matplotlib.rc('font', family='Microsoft JhengHei')

def log(message):
    print(message)

def joblist_url(url, page, progress, root):
    log("joblist_url called")
    joblist = []
    page_num = 1
    while page_num <= page:
        current_url = url.replace('page=1', f'page={page_num}')
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
        
        page_num += 1
        root.after(0, progress.step, 100 / page)  
    print(len(joblist))
    return joblist

def getinfo(joblist, progress, root):
    log("getinfo called")
    skills_list = []
    total_jobs = len(joblist)
    for i, work_url in enumerate(joblist):
        if not work_url.startswith('http'):
            work_url = 'https://' + work_url
            
        work = requests.get(work_url)
        soup = bs4(work.text, 'lxml')
        
        skill_blocks = soup.find_all('a', class_='tools text-gray-deep-dark d-inline-block')
        for skill_block in skill_blocks:
            u_tag = skill_block.find('u')
            if u_tag:
                skill = u_tag.text.strip()
                skills_list.append(skill)
                
        root.after(0, progress.step, 100 / total_jobs) 

    return skills_list

def analyze(skills_list):
    log("analyze called")
    skill_counts = {}
    for skill in skills_list:
        if skill in skill_counts:
            skill_counts[skill] += 1
        else:
            skill_counts[skill] = 1
    df = pd.DataFrame(list(skill_counts.items()), columns=['技能', '次數'])
    df = df.sort_values(by='次數', ascending=False)
    df = df.head(10)  
    return df

def create_figure(df):
    fig = Figure(figsize=(8, 6), dpi=100)  
    ax = fig.add_subplot(111)
    bars = ax.bar(df['技能'], df['次數'], width=0.5)  
    ax.set_xlabel('技能', fontproperties=zh_font, fontsize=12)  
    ax.set_ylabel('次數', fontproperties=zh_font, fontsize=12)  
    ax.set_title('技能次數直方圖', fontproperties=zh_font, fontsize=14)  
    fig.tight_layout()  
    return fig

def start_analysis(keyword_entry, page_entry, exp_var, progress, result_text, root, canvas_placeholder):
    log("start_analysis called")
    keyword = keyword_entry.get()
    page = int(page_entry.get())
    exp_value = exp_var.get()  
    
    exp_dict = {
        "一年以下": "1",
        "一至三年": "3",
        "三至五年": "5",
        "五至十年": "10",
        "十年以上": "99"
    }
    exp = exp_dict[exp_value]
    
    encoded_keyword = quote(keyword)
    base_url = 'https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword=ENCODED_KEYWORD&expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=12&asc=0&page=1&jobexp=EXP&mode=s&jobsource=index_s&langFlag=0&langStatus=0&recommendJob=1&hotJob=1'
    url = base_url.replace('ENCODED_KEYWORD', encoded_keyword)
    url = url.replace('EXP', exp)
    
    progress['value'] = 0  
    
    def run_analysis():
        joblist = joblist_url(url, page, progress, root)
        skills_list = getinfo(joblist, progress, root)
        df = analyze(skills_list)
        
        result_text.delete('1.0', tk.END)  
        
        result_text.insert(tk.END, f"搜尋{len(joblist)}筆職缺的前十名技能\n")
        result_text.insert(tk.END, df.to_string(index=False))  
        
        fig = create_figure(df)
        canvas = FigureCanvasTkAgg(fig, master=canvas_placeholder)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=2, rowspan=9, padx=10, pady=5)
    
    threading.Thread(target=run_analysis).start()

def input_and_analyze():
    log("input_and_analyze called")
    root = tk.Tk()
    root.title('104 Job Skills Analyzer')
    
    keyword_label = ttk.Label(root, text='關鍵字：')
    keyword_label.grid(row=0, column=0, sticky=tk.E)
    keyword_entry = ttk.Entry(root, width=10)
    keyword_entry.grid(row=0, column=1, padx=(0,10), pady=5, sticky=tk.W)
    
    page_label = ttk.Label(root, text='總頁數：')
    page_label.grid(row=1, column=0, sticky=tk.E)
    page_entry = ttk.Entry(root, width=10)
    page_entry.grid(row=1, column=1, padx=(0,10), pady=5, sticky=tk.W)
    
    exp_label = ttk.Label(root, text='年資：')
    exp_label.grid(row=2, column=0, sticky=tk.E)
    
    exp_var = tk.StringVar()  
    exp_combobox = ttk.Combobox(root, textvariable=exp_var, values=["一年以下", "一至三年", "三至五年", "五至十年", "十年以上"])
    exp_combobox.grid(row=2, column=1, padx=(0,10), pady=5, sticky=tk.W)
    exp_combobox.current(0)  
    
    analyze_button = ttk.Button(root, text='開始分析', command=lambda: start_analysis(keyword_entry, page_entry, exp_var, progress, result_text, root, canvas_placeholder))
    analyze_button.grid(row=3, columnspan=2, pady=10)
    
    progress = ttk.Progressbar(root, orient='horizontal', mode='determinate')
    progress.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
    
    result_label = ttk.Label(root, text='分析結果：')
    result_label.grid(row=5, column=0, sticky=tk.E)
    
    result_text = tk.Text(root, width=50, height=10)
    result_text.grid(row=6, column=0, columnspan=2, padx=10, pady=5)
    
    canvas_placeholder = tk.Frame(root)  
    canvas_placeholder.grid(row=0, column=2, rowspan=7, padx=10, pady=5)
    
    root.mainloop()

input_and_analyze()
