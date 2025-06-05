import sys # внешние аргументы
import requests # для получения html страницы и ее текста
from bs4 import BeautifulSoup # парсим страницу
import subprocess # позволяет из Python запускать системные команды



def input_processing():
    pkg_name = ""

    if len(sys.argv) < 2:
        print("Использование: python main.py <имя_пакета>")
        print("Введите имя пакета")
        input_processing()

    pkg_name = sys.argv[1]
    print(f"Вы передали пакет: {pkg_name}")

    return pkg_name  



def get_html(url):
    response = requests.get(url)

    if response.status_code < 200 or response.status_code > 299:
        print("Не удалось получить страницу, код:", response.status_code)
        return None
    
    return response



def find_table(response):
    if response == None:
        return None
    
    results_table = None

    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")

    for table in soup.find_all("table"):
        for header in table.find_all("tr"):
            th = header.find("th")
            if not th:
                continue
            a = th.find("a")
            if a and a.get_text(strip=True) == "NVR":
                results_table = table
                break

        if results_table:
            break

    return results_table



def pars_html(results_table, all_pkgs):
    if not results_table:
        print("Не удалось найти таблицу с результатами на странице.")
        return []
    
    rows = results_table.find_all("tr")

    for row in rows:
        td = row.find("td")
        if not td:
            continue
        a = td.find("a", href=True)
        if a and "buildID=" in a["href"]:
            _, id = a["href"].split("=")
            name = a.get_text(strip=True)
            all_pkgs.append({
                "name": name,
                "id": id 
            })



def get_pkgs(pkg_name):
    all_pkgs = []
    url = f"https://koji.fedoraproject.org/koji/search?match=glob&type=package&terms={pkg_name}"

    while True:
        response = get_html(url)
        if not response: return

        results_table = find_table(response)
        if not results_table: return
        
        pars_html(results_table, all_pkgs)

        next = results_table.find("a", string=">>>")

        if not next:
            break

        url = "https://koji.fedoraproject.org/koji/" + next["href"]
    
    return all_pkgs



def choose_candidate(all_pkgs):
    if not all_pkgs:
        print("Не найдено ни одного пакета с таким именем.")
        return None
    
    selected = None
    candidates = [p for p in all_pkgs if ".fc" in p["name"]]

    if not candidates:
        print("Не найдено ни одной сборки с суффиксом '.fc'.")
        return None
    
    i = 1
    numbers = []
    print("\nНайдены следующие кандидаты на установку (суффикс '.fc'):\n")
    for pkg in candidates:
        numbers.append(str(i))
        print(f"  {i}. {pkg['name']}")
        i += 1

    while True:
        print("\nВведите номер пакета, который хотите установить:")
        res = input()
        if res in numbers:
            res = int(res)
            selected = candidates[res - 1]
            print(f"\nВы выбрали: {selected['name']}")
            return selected
        else:
            print("\nНекорректный ввод: нужно ввести целое число от 1 до", len(candidates))



def is_package_installed(name):
    output = subprocess.check_output(["rpm", "-qa"], universal_newlines=True) # universal_newlines=True - Преобразует выход (stdout) команды из bytes в str

    for line in output.splitlines():
        if name in line:
            return line
    
    return False



def remove_package(name):
    print(f"\nУдаляем пакет {name}...")
    error = subprocess.call(["sudo", "dnf", "remove", name, "-y"], stdout=subprocess.DEVNULL)
    if error:
        print("Ошибка при удалении пакета.")
    else:
        print(f"Пакет успешно удалён.")



def install(id):
    print("\nНачинаем скачивание пакета...")
    url_down = ""
    url = "https://koji.fedoraproject.org/koji/buildinfo?buildID=" + id
    response = get_html(url)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    for l in links:
        if sys.argv[1] in l["href"] and "aarch64.rpm" in l["href"] and "fc39" in l["href"]:
            url_down = l["href"]
            break
    
    if url_down == "":
        print("Не обнаружилось нужной ссылки для скачивания :(")
        return 
    
    response = get_html(url_down)
    if response:
        filename = url_down.split("/")[-1]
        with open(filename, "wb") as f:
            f.write(response.content)
        
        err = subprocess.call(["sudo", "dnf", "install", "-y", filename], stdout=subprocess.DEVNULL)
        if err == 0:
             print("\nПакет успешно установлен!")
        else:
            print("\nОшибка при установке RPM")



def processing(selected):
    if not selected:
        return None
    
    name = selected['name']
    
    installed_fullname = is_package_installed(name)
    if is_package_installed(name):
        print(f"\nПакет {name} уже установлен в системе как \"{installed_fullname}\".")
        print("Хотите удалить его? (Y/N)")
        answer = input()
        if answer == "y" or answer == "Y":
            remove_package(name)

    install(selected["id"])


def main():
    pkg_name = input_processing()
    all_pkgs = get_pkgs(pkg_name)
    selected = choose_candidate(all_pkgs)
    processing(selected)

    



if __name__ == "__main__":
    main()
