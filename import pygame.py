import pygame
import sys

# تهيئة مكتبة Pygame
pygame.init()

# أبعاد الشاشة
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("لعبة بونج الجماعية - لاعبين")

# الألوان المستخدمة
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
RED = (255, 100, 100)

# إعدادات المضارب والكرة
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
BALL_SIZE = 15

# أماكن اللاعبين الابتدائية
player1_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
player2_y = HEIGHT // 2 - PADDLE_HEIGHT // 2

# موقع الكرة وسرعتها الابتدائية
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_speed_x = 5
ball_speed_y = 5

# النقاط
score1 = 0
score2 = 0

# سرعة تحرك المضارب
paddle_speed = 7

# ساعة التحكم بمعدل الإطارات
clock = pygame.time.Clock()

# تحديد الخطوط لعرض النتيجة
font = pygame.font.Font(None, 74)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # استقبال مدخلات لوحة المفاتيح
    keys = pygame.key.get_pressed()

    # تحكم اللاعب الأول (اليسار): مفاتيح W للأعلى و S للأسفل
    if keys[pygame.K_w] and player1_y > 0:
        player1_y -= paddle_speed
    if keys[pygame.K_s] and player1_y < HEIGHT - PADDLE_HEIGHT:
        player1_y += paddle_speed

    # تحكم اللاعب الثاني (اليمين): الأسهم للأعلى وللأسفل
    if keys[pygame.K_UP] and player2_y > 0:
        player2_y -= paddle_speed
    if keys[pygame.K_DOWN] and player2_y < HEIGHT - PADDLE_HEIGHT:
        player2_y += paddle_speed

    # تحريك الكرة
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # ارتداد الكرة من الحواف العلوية والسفلية لشاشة اللعب
    if ball_y <= 0 or ball_y >= HEIGHT - BALL_SIZE:
        ball_speed_y *= -1

    # تصادم الكرة مع مضرب اللاعب الأول (اليسار)
    if ball_x <= 30 and player1_y < ball_y < player1_y + PADDLE_HEIGHT:
        ball_speed_x *= -1
        # زيادة السرعة بنسبة بسيطة لزيادة الحماس
        ball_speed_x *= 1.05
        ball_speed_y *= 1.05

    # تصادم الكرة مع مضرب اللاعب الثاني (اليمين)
    if ball_x >= WIDTH - 30 - BALL_SIZE and player2_y < ball_y < player2_y + PADDLE_HEIGHT:
        ball_speed_x *= -1
        ball_speed_x *= 1.05
        ball_speed_y *= 1.05

    # تسجيل النقاط وإعادة الكرة للمنتصف في حال الخسارة
    if ball_x < 0:
        score2 += 1
        ball_x, ball_y = WIDTH // 2, HEIGHT // 2
        ball_speed_x, ball_speed_y = 5, 5  # إعادة ضبط السرعة للوضع الطبيعي

    if ball_x > WIDTH:
        score1 += 1
        ball_x, ball_y = WIDTH // 2, HEIGHT // 2
        ball_speed_x, ball_speed_y = -5, 5

    # رسم العناصر على الشاشة
    screen.fill(BLACK)

    # رسم مضرب اللاعب الأول واللاعب الثاني
    pygame.draw.rect(screen, BLUE, (15, player1_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.rect(screen, RED, (WIDTH - 15 - PADDLE_WIDTH, player2_y, PADDLE_WIDTH, PADDLE_HEIGHT))

    # رسم الكرة الخط الفاصل
    pygame.draw.ellipse(screen, WHITE, (ball_x, ball_y, BALL_SIZE, BALL_SIZE))
    pygame.draw.aaline(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

    # عرض النتائج
    text_score1 = font.render(str(score1), True, BLUE)
    screen.blit(text_score1, (WIDTH // 4, 20))

    text_score2 = font.render(str(score2), True, RED)
    screen.blit(text_score2, (3 * WIDTH // 4 - text_score2.get_width() // 2, 20))

    # تحديث الشاشة وضبط الإطارات (60 إطار بالثانية)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()