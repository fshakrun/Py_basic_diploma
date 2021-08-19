import pprint
import datetime
import json
from urllib.parse import urljoin
import requests


class Picture:
    name = ''

    def __init__(self, date, likes, sizes):
        self.date = date
        self.likes = likes
        self.sizes = sizes
        self.size_type = sizes['type']
        self.url = sizes['url']
        self.maxsize = max(sizes['width'], sizes['height'])

    def __repr__(self):
        return f'date: {self.date}, likes: {self.likes}, size: {self.maxsize}, url: {self.url}'


class VkApi:
    BASE_URL = "https://api.vk.com/method/"

    @staticmethod
    def find_hugest(sizes):
        sizes_chart = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for chart in sizes_chart:
            for size in sizes:
                if size['type'] == chart:
                    return size

    # здесь должен быть токен и версия приложения vk
    def __init__(self):
        self.token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
        self.version = '5.124'

    def get_pictures(self, uid, qty):
        get_url = urljoin(self.BASE_URL, 'photos.get')
        response = requests.get(get_url, params={
            'access_token': self.token,
            'v': self.version,
            'owner_id': uid,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1
        }).json().get('response').get('items')

        return sorted([Picture(photo.get('date'),
                               photo.get('likes')['count'],
                               self.find_hugest(photo.get('sizes'))) for photo in response],
                      key=lambda p: p.maxsize, reverse=True)[:qty]


class YanApi:
    @staticmethod
    def create_file_names(photos):
        for photo in photos:
            photo.name = str(photo.likes)
            if [p.likes for p in photos].count(photo.likes) > 1:
                photo.name += '_' + str(photo.date)
            photo.name += '.jpg'

    @staticmethod
    def check_folder_name(n_folder, ex_folders):
        if n_folder not in ex_folders:
            return n_folder
        n = 1
        n_folder += '_' + str(n)
        while n_folder in ex_folders:
            n_folder = n_folder.replace('_' + str(n), '_' + str(n + 1))
            n += 1
        return n_folder

    def __init__(self, token: str):
        self.auth = f'OAuth {token}'

    def get_folders(self):
        return [a['name'] for a in (requests.get("https://cloud-api.yandex.net/v1/disk/resources",
                                                 params={"path": '/'},
                                                 headers={"Authorization": self.auth})
                                    .json().get('_embedded').get('items')) if a['type'] == 'dir']

    def creating_folder(self, folder_name):
        resp = requests.put("https://cloud-api.yandex.net/v1/disk/resources",
                            params={"path": '/' + folder_name},
                            headers={"Authorization": self.auth})
        print(f'Создаем папку"{folder_name}":' + str(resp.status_code))
        return resp.ok

    def upload(self, uid, photos):
        upload_folder = self.check_folder_name(uid, self.get_folders())
        self.create_file_names(photos)
        if self.create_folder(upload_folder):
            log_result = []
            for photo in photos:
                response = requests.post("https://cloud-api.yandex.net/v1/disk/resources/upload",
                                         params={"path": '/' + upload_folder + '/' + photo.name,
                                                 "url": photo.url},
                                         headers={"Authorization": self.auth})
                if response.status_code == 202:
                    print(f'Фото"{photo.name}"загружено.')
                    log_result.append({"file_name": photo.name, "size": photo.size_type})
                else:
                    print(f'При загрузке "{photo.name}" произошла ошибка: '
                          f'{response.json().get("message")}. Status code: {response.status_code}')
            with open(f'{uid}_{datetime.now().strftime("%m_%d_%Y_%H_%M_%S")}_files.json', "w") as f:
                json.dump(log_result, f, indent=2)

    def create_folder(self, upload_folder):
        pass


def init():
    yandex_token = input('Введите ваш токен от Я.Диска: ')
    uid = input('VK user id: ')
    qty = input('Количество фотографий: ')
    vk_api = VkApi()
    ya_api: YanApi = YanApi(yandex_token)
    ya_api.upload(uid, vk_api.get_pictures(uid, qty))


if __name__ == '__main__':
    init()
