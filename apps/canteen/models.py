# Django Modules
from django.db.models import (
    Model, 
    OneToOneField,
    CASCADE,
    CharField,
    BooleanField,
    ForeignKey,
    TextField,
    DecimalField,
    IntegerField,
    URLField,
    DateField,
    ManyToManyField,
    UniqueConstraint,
    )
from django.core.exceptions import ValidationError

# Project Modules
from apps.abstracts.models import AbstractBaseModel
from apps.auths.models import School
from apps.auths.models import CustomUser


class Canteen(AbstractBaseModel):

    CANTEEN_NAME_MAX_LENGTH = 150
    
    school = OneToOneField(
        School,
        on_delete=CASCADE,
        related_name='canteen',
        verbose_name="School"
    )
    name = CharField(
        max_length=CANTEEN_NAME_MAX_LENGTH, 
        verbose_name="Canteen's Name"
    )
    is_open = BooleanField(
        default=True, 
        verbose_name="Open"
    )

    def __str__(self):
        return f"Canteen: {self.name} ({self.school.name})"

# Чтобы меню было структурированным (Первое, Второе, Напитки).
class FoodCategory(AbstractBaseModel):

    FOOD_CATEGORY_MAX_LENGTH = 100

    name = CharField(
        max_length=FOOD_CATEGORY_MAX_LENGTH, 
        verbose_name="Category"
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Food Categories"
    

class Dish(AbstractBaseModel):

    DISH_NAME_MAX_LENGTH=150
    PRICE_MAX_LENGTH=10

    category = ForeignKey(
        FoodCategory, 
        on_delete=CASCADE, 
        related_name='dishes'
    )
    name = CharField(
        max_length=DISH_NAME_MAX_LENGTH, 
        verbose_name="Dish's name"
    )
    description = TextField(
        blank=True, 
        verbose_name="Description and Composition"
    )
    price = DecimalField(
        max_digits=PRICE_MAX_LENGTH, 
        decimal_places=2, 
        verbose_name="Price"
    )
    calories = IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Калории"
    )
    image = URLField(
        blank=True, 
        null=True, 
        verbose_name="Фото блюда"
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Dishes'


class DailyMenu(AbstractBaseModel):
    canteen = ForeignKey(
        Canteen, 
        on_delete=CASCADE, 
        related_name='menus'
    )
    date = DateField(
        verbose_name="Date Menu"
    )
    dishes = ManyToManyField(
        Dish, 
        related_name='daily_menus', 
        verbose_name="Today's dishes"
    )

    class Meta:
        unique_together = ('canteen', 'date') # Чтобы нельзя было создать два меню на один день для одной столовой

    def __str__(self):
        return f"Menu for {self.date} - {self.canteen.school.name}"


class Comment(AbstractBaseModel):
    """Student commentary on a dish or daily menu"""

    COMMENT_MAX_LENGTH = 1000

    # Автор комментария
    author = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='comments',
        verbose_name="Author"
    )
    # Комментарий можно оставить к конкретному блюду...
    dish = ForeignKey(
        Dish,
        on_delete=CASCADE,
        related_name='comments',
        null=True,
        blank=True,
        verbose_name="Dish"
    )
    # ...или к дневному меню в целом
    daily_menu = ForeignKey(
        DailyMenu,
        on_delete=CASCADE,
        related_name='comments',
        null=True,
        blank=True,
        verbose_name="Daily Menu"
    )
    text = TextField(
        max_length=COMMENT_MAX_LENGTH,
        verbose_name="Comment"
    )
    is_visible = BooleanField(
        default=True,
        verbose_name="Visible"
    )

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['-created_at']  # из AbstractBaseModel

    def __str__(self):
        target = self.dish or self.daily_menu
        return f"{self.author} → {target}: {self.text[:50]}"

    def clean(self):
        # Нельзя одновременно указать и блюдо, и меню — и нельзя не указать ничего
        if not self.dish and not self.daily_menu:
            raise ValidationError("Укажите блюдо или меню.")
        if self.dish and self.daily_menu:
            raise ValidationError("Выберите что-то одно: блюдо или меню.")


class ReactionType(AbstractBaseModel):
    """Reaction type: 👍 Tasty, 😐 Normal, 👎 Not tasty - can be expanded"""

    LABEL_MAX_LENGTH = 50
    EMOJI_MAX_LENGTH = 10

    label = CharField(
        max_length=LABEL_MAX_LENGTH,
        verbose_name="Label"         # например: "Вкусно"
    )
    emoji = CharField(
        max_length=EMOJI_MAX_LENGTH,
        verbose_name="Emoji",        # например: "👍"
        blank=True
    )

    def __str__(self):
        return f"{self.emoji} {self.label}"


class DishReaction(AbstractBaseModel):
    """Student reaction to a dish (one student - one reaction to a dish)"""

    user = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='dish_reactions',
        verbose_name="Student"
    )
    dish = ForeignKey(
        Dish,
        on_delete=CASCADE,
        related_name='reactions',
        verbose_name="Dish"
    )
    reaction_type = ForeignKey(
        ReactionType,
        on_delete=CASCADE,
        related_name='dish_reactions',
        verbose_name="Reaction"
    )

    class Meta:
        verbose_name = "Dish Reaction"
        verbose_name_plural = "Dish Reactions"
        constraints = [
            UniqueConstraint(
                fields=['user', 'dish'],
                name='unique_dish_reaction_per_user'
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.dish}: {self.reaction_type}"


class MenuReaction(AbstractBaseModel):
    """A student's reaction to the daily menu"""

    user = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='menu_reactions',
        verbose_name="Student"
    )
    daily_menu = ForeignKey(
        DailyMenu,
        on_delete=CASCADE,
        related_name='reactions',
        verbose_name="Daily Menu"
    )
    reaction_type = ForeignKey(
        ReactionType,
        on_delete=CASCADE,
        related_name='menu_reactions',
        verbose_name="Reaction"
    )

    class Meta:
        verbose_name = "Menu Reaction"
        verbose_name_plural = "Menu Reactions"
        constraints = [
            UniqueConstraint(
                fields=['user', 'daily_menu'],
                name='unique_menu_reaction_per_user'
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.daily_menu}: {self.reaction_type}"
