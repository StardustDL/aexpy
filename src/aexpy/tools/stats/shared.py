from ...models import Product


def duration(data: Product):
    return data.duration.total_seconds()


def success(data: Product):
    return int(data.success)
