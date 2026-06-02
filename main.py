# Импорты
import nodriver as uc
import os
import re
from markdownify import markdownify as md
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()

OBSIDIAN_PATH = os.getenv("OBSIDIAN_PATH")
STANDART_PAGE = os.getenv("STANDART_PAGE")


# Главная функция
async def main():
    # Получает стандартную новостную страницу
    browser = await uc.start(headless=True)
    standart_page = await browser.get(STANDART_PAGE)

    # Берет все элементы с ссылками на новостную страницу
    elements = await standart_page.select_all(".b_ear.m_list")
    links = get_links(elements)
    
    # Вызывает основную функцию для создания записей
    await article(browser, links)


# Получает первые 50 ссылок из списка элементов
def get_links(elems) -> list:
    linkes = []

    for obj in elems:
        a_link = str(obj.get_html).split('"')[1].split("https://")

        if len(a_link) == 1:
            link = f"{STANDART_PAGE}{str(obj.get_html).split('"')[1]}"
        else: link = f"https://{a_link[1]}"

        linkes.append(link)

    return linkes


# Основная функция, проходящая по ссылкам и записывающая данные со страницы в .md файл
async def article(browser, links) -> None:
    try:
        for link in links:    
            page = await browser.get(link)
            
            # Очищает имя файла и создает путь к нему
            filename = sanitize_filename(str((await page.select(".subheader")).text))
            filepath = f"{OBSIDIAN_PATH}{filename}.md"

            # вызов функции для получения информации со страницы 
            text = await get_template(page)

            # Сохраняет запись в .md файл
            save_article(text, filepath)

    except Exception as error:
        print(f"Ошибка в article: f{error}")

# Очистка имени файла от запрещенных символов
def sanitize_filename(name) -> str:
    return re.sub(r'[\\/*,.?:"<>|]', "", name).strip()


# Получает данные со страницы
async def get_template(page) -> str:
    header = str((await page.select("h1.headline")).text)
    date = (await page.select("time.time")).text
    main_text = md(str(await page.select(".b_article-text")))

    text = f"{header}\nДата создания: {date}\n\n{main_text}\n\nЗависимости: "

    # Получает зависимости со страницы и записывает их в конец файла
    names = await get_standart_names_in_page(page)
    for name in names:
        text += f"[[{name}]] "
    
    return text


# Получает зависимости на странице и врзвращает массив 
async def get_standart_names_in_page(new_page) -> list:
    names = []
    try:
        standart_names = await new_page.select_all("a.tag")
        for name in standart_names:
            names.append(name.text)
    except Exception as error:
        print(f"Ошибка при получание зависимостей: {error}")

    return names

        
# Сохраняет .md файл
def save_article(text, filepath):
    with open(filepath, "w") as file:
        file.write(text)


if __name__ == "__main__":
    uc.loop().run_until_complete(main())