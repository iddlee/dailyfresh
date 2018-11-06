from django.contrib import admin
from apps.goods.models import *


admin.site.register([GoodsType, GoodsSKU, Goods, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner])
