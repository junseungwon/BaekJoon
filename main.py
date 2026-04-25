#!/usr/bin/env python
import os
import time

import requests
import cloudscraper
from bs4 import BeautifulSoup as bs

user_id = input("Enter Baekjoon ID : ")
judge_key = input("Enter Cookies/OnlineJudge : ")

# 초기 변수 설정
base_url = "https://www.acmicpc.net"  # 루트 도메인
url = f"https://www.acmicpc.net/status?user_id={user_id}&result_id=4"

cookie = {
    "OnlineJudge": judge_key
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
}


def get_next_page(url):
    try:
        s = requests.session()  # 세션 유지용
        req = s.get(url, cookies=cookie, headers=headers)
        soup = bs(req.text, "html.parser")
        next_page = soup.select_one("#next_page")['href']  # 다음 페이지 버튼
        result = base_url + next_page
        return result
    except Exception as e:  # 오류 발생시 다음페이지가 없는것으로 간주함.
        return False


def get_sorting(solve_num):
    source_url = "https://www.acmicpc.net/problem/" + solve_num
    req = s.get(source_url, cookies=cookie, headers=headers)
    soup = bs(req.text, "html.parser")
    sorting = soup.select("#problem_tags > ul > li > a")

    folder_name = ""
    separator = ", "  # 구분자

    for element in sorting:
        folder_name += element.get_text() + separator
    folder_name = folder_name.strip()[0:-1].strip()  # 맨 끝에 구분자 지우기
    return folder_name


TIER_NAMES = [
    "Unrated",
    "Bronze 5", "Bronze 4", "Bronze 3", "Bronze 2", "Bronze 1",
    "Silver 5", "Silver 4", "Silver 3", "Silver 2", "Silver 1",
    "Gold 5", "Gold 4", "Gold 3", "Gold 2", "Gold 1",
    "Platinum 5", "Platinum 4", "Platinum 3", "Platinum 2", "Platinum 1",
    "Diamond 5", "Diamond 4", "Diamond 3", "Diamond 2", "Diamond 1",
    "Ruby 5", "Ruby 4", "Ruby 3", "Ruby 2", "Ruby 1",
]


scraper = cloudscraper.create_scraper()


def get_tier(solve_num):
    """solved.ac API로 문제 난이도를 가져온다."""
    try:
        resp = scraper.get(f"https://solved.ac/api/v3/problem/show?problemId={solve_num}")
        if resp.status_code == 200:
            level = resp.json().get("level", 0)
            return TIER_NAMES[level] if level < len(TIER_NAMES) else "Unknown"
    except:
        pass
    return "Unrated"


def get_problem_info(solve_num):
    """문제 페이지에서 제목, 문제 설명, 입력, 출력, 예제를 추출한다."""
    problem_url = "https://www.acmicpc.net/problem/" + solve_num
    req = s.get(problem_url, cookies=cookie, headers=headers)
    soup = bs(req.text, "html.parser")

    title = ""
    description = ""
    input_desc = ""
    output_desc = ""
    examples = []

    try:
        title = soup.select_one("#problem_title").get_text().strip()
    except:
        pass
    try:
        description = soup.select_one("#problem_description").get_text().strip()
    except:
        pass
    try:
        input_desc = soup.select_one("#problem_input").get_text().strip()
    except:
        pass
    try:
        output_desc = soup.select_one("#problem_output").get_text().strip()
    except:
        pass

    # 예제 입출력 추출
    i = 1
    while True:
        sample_in = soup.select_one(f"#sample-input-{i}")
        sample_out = soup.select_one(f"#sample-output-{i}")
        if sample_in is None:
            break
        examples.append((sample_in.get_text().strip(), sample_out.get_text().strip() if sample_out else ""))
        i += 1

    return title, description, input_desc, output_desc, examples


def get_source(url):
    source_url = url

    req = s.get(source_url, cookies=cookie, headers=headers)
    soup = bs(req.text, "html.parser")
    source_code = soup.select_one("#source").get_text()  # 추출한 소스코드
    return source_code


def get_lang_extension(language):
    if language == "Python 3" or language == "PyPy3":
        return "py"
    elif language == "C99":
        return "c"
    elif language.startswith("C++"):
        return "cpp"
    elif language.startswith("Java"):
        return "java"
    elif language.startswith("C#"):
        return "cs"
    else:
        return "txt"


def write_file(queue):
    # [정렬순서] 내림차순 :: 제출번호 -> 오름차순 :: 시간 -> 메모리
    sorted_queue = sorted(queue, key=lambda x: (-x[0], x[2], x[1]))
    save_num = None
    for edit_num, memory, timec, solve_num, language, source_code, problem_info, tier in sorted_queue:
        if solve_num == save_num:  # 번호가 겹침
            pass
        else:
            ext = get_lang_extension(language)

            download_folder = os.path.join("downloads", user_id)
            try:
                if not os.path.exists(download_folder):
                    os.makedirs(download_folder)
            except OSError:
                print('Error: Creating directory. ' + download_folder)
            file_path = os.path.join(download_folder, f"{solve_num}.md")

            if os.path.isfile(file_path):
                print(f"{solve_num}번. 파일 중복으로 Pass 합니다.")
            else:
                title, description, input_desc, output_desc, examples = problem_info

                content = f"# {solve_num}번 - {title}\n\n"
                content += f"**난이도: {tier}**\n\n"
                content += f"## 문제\n{description}\n\n"
                if input_desc:
                    content += f"## 입력\n{input_desc}\n\n"
                if output_desc:
                    content += f"## 출력\n{output_desc}\n\n"
                for idx, (si, so) in enumerate(examples, 1):
                    content += f"## 예제 입력 {idx}\n```\n{si}\n```\n\n"
                    content += f"## 예제 출력 {idx}\n```\n{so}\n```\n\n"
                content += f"---\n\n"
                content += f"## 소스코드 ({language})\n```{ext}\n{source_code}\n```\n"

                f = open(file_path, 'w', encoding='utf-8')
                f.write(content)
                f.close()
                print(f"{solve_num}번 처리 완료, 언어 {language}")
        save_num = solve_num


if __name__ == "__main__":
    s = requests.session()  # 세션 유지용
    while True:
        # 채점 현황 - 맞았습니다로 이동함.
        req = s.get(url, cookies=cookie, headers=headers)
        soup = bs(req.text, "html.parser")

        # 소스코드 추출 & 저장
        a_tag = soup.select('td > a:nth-child(2)')

        queue = []
        for element in a_tag:
            href = str(element['href'])  # 언어/수정 에서 언어부분은 무시하고 수정부분만 본다.
            if not "problem" in href:
                try:
                    # 문제 세부 사항 추출
                    solve_num = href.split("/")[2]  # 문제 번호
                    edit_num = href.split("/")[3]  # 수정번호 (제출 번호)
                    memory = soup.select_one(f"#solution-{edit_num} > td.memory").get_text()  # 메모리
                    timec = soup.select_one(f"#solution-{edit_num} > td.time").get_text()  # 시간
                    language = soup.select(f"#solution-{edit_num} > td > a:nth-child(1)")[1].get_text()  # 푼 언어

                    # 문제가 어디에 분류되어 있는지 추출
                    folder_name = get_sorting(solve_num)

                    # 문제 정보 추출
                    problem_info = get_problem_info(solve_num)

                    # 난이도 추출
                    tier = get_tier(solve_num)

                    # 소스코드 추출
                    source_code = get_source(base_url + href)  # 수정 버튼 누르면 나오는 url 제공

                    queue.append((int(edit_num), int(memory), int(timec), solve_num, language,
                                  source_code, problem_info, tier))  # queue에 처리할 것을 저장한다.
                    print(f"문제 {solve_num}번 추출 완료")
                except:
                    pass

                    # Queue에 있는것을 처리한다.
        write_file(queue)

        # 다음 페이지로 이동
        url = get_next_page(url)
        if url == False:
            break  # 다음페이지 없으면 반복 멈춤.
        time.sleep(0.5)  # 서버를 위한 delay
    print("처리가 완료 되었습니다.")
