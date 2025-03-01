
import sensor, image, time,math

import random
from machine import UART
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)








uart = UART(3, 9600)
uart.init(9600, bits=8, parity=None, stop=1)
# type 01:机器人应该下的格子; value 01-09: 机器人应该下的格子 0x01-0x09
# type 02:下棋得出结果; value 01:黑胜 02:白胜 03:平局
# type 03:棋盘旋转角度; value 角度值（十六进制）
# type 04:人为挪动棋子; value 该棋子原来的格子序号*10+现在的格子序号（16进制）
# type 05:收到信息后的确认帧; value 00:模式选择 01:人机对战 02:人人对战 03:人下棋 04:机器下棋 05:人下棋 06:机器下棋
def sending_data(type,value):
    global uart


    data = bytearray([0x60,type,value,0x3b])
    print(data)
    uart.write(data);

#---------------------------------------------------------
# 初始化棋盘数据，黑方为1，白方为2   01 黑圣，02白胜，03 平局 04必胜
qipan = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
# 记录棋盘之前的状态，方便检查是否悔棋或者认为挪动棋子
olde_qipan = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
# 记录下棋的次数，方便计算输赢
step = 0
# 扫描棋盘是否达成一方胜利或和棋
def if_victory(f):
    result = -1
    # 检查横向和纵向
    for i in range(3):

        if qipan[i][0] == qipan[i][1] == qipan[i][2] and qipan[i][2] != 0:
            result = qipan[i][0]
        if qipan[0][i] == qipan[1][i] == qipan[2][i] and qipan[2][i] != 0:
            result = qipan[0][i]
#    print("heng  ",qipan[0][1], qipan[2][1], qipan[1][1],"result",result)
    # 检查对角线
    if qipan[0][0] == qipan[1][1] == qipan[2][2] and qipan[2][2] != 0:
        result = qipan[0][0]
    if qipan[0][2] == qipan[1][1] == qipan[2][0] and qipan[2][0]  != 0:
        result = qipan[0][2]
    # 平局
    if result == -1 and step == 8:
        if f == 0:
            sending_data(0x02,0x03)
        return 3
    if result != -1:
        if f == 0:
            sending_data(0x02,result)
        return result

    return -1


def check_before(role):
#    if step == 7:   # 提前检查
#        for i in range(0, 3):
#            for j in range(0, 3):
#                if qipan[i][j] == 0:
#                    qipan[i][j] = role
#                    return if_victory(0)
    return -1

# 下棋策略；返回：下棋的位置在棋盘列表中的索引对
def computer_move(role):
    global flag_special
    if role == 1:
        duis = 2
    else:
        duis = 1


    # 寻找自己的获胜机会
    for i in range(3):
        for j in range(3):
            if qipan[i][j] == 0:
                qipan[i][j] = role  # 假设在该位置尝试落子
                if if_victory(1) == role:
                    qipan[i][j] = 0  # 恢复棋盘状态
                    return i, j  # 如果落子可以获胜，则直接落子并返回
                qipan[i][j] = 0  # 恢复棋盘状态

    # 防守对手可能的获胜
    for i in range(3):
        for j in range(3):
            if qipan[i][j] == 0:
                qipan[i][j] = duis  # 假设在该位置尝试落子
                t = if_victory(1)
                if t == duis:
                    qipan[i][j] = 0  # 恢复棋盘状态
                    return i, j  # 如果落子可以防守对手获胜，则直接落子并返回
                qipan[i][j] = 0  # 恢复棋盘状态



    # 优先下正中心
    if qipan[1][1] == 0:
        return 1, 1

    if qipan[0][0] == role:
        if qipan[0][2] == 0 and qipan[0][1] ==0:
            return 0, 2
        elif qipan[2][0] == 0 and qipan[1][0] ==0:
            return 2,0
    elif qipan[0][2] == role:
        if qipan[0][0] == 0 and qipan[0][1] ==0:
            return 0, 0
        elif qipan[2][2] == 0 and qipan[1][2] ==0:
            return 2,2
    elif qipan[2][0] == role:
        if qipan[0][0] == 0 and qipan[1][0] ==0:
            return 0, 0
        elif qipan[2][2] == 0 and qipan[2][1] ==0:
            return 2,2
    elif qipan[2][2] == role:
        if qipan[0][2] == 0 and qipan[1][2] ==0:
            return 0, 2
        elif qipan[2][0] == 0 and qipan[2][1] ==0:
            return 2,0

    # 优先下对角线
    if qipan[0][0] == 0:
        return 0, 0
    elif qipan[0][2] == 0:
        return 0, 2
    elif qipan[2][0] == 0:
        return 2, 0
    elif qipan[2][2] == 0:
        return 2, 2

    # 随机选择一个空位置落子

    for i in range(3):
        for j in range(3):
            if qipan[i][j] == 0:
                return i,j




def check_special():
    global flag_special
#    if qipan[0][0] == 1 and (qipan[1][2]==2 or qipan[2][1]==2 ):
#        sending_data(0x02,0x04)
#        flag_special = 4
#    elif qipan[0][2] == 1 and (qipan[1][0]==2 or qipan[2][1]==2 ):
#        sending_data(0x02,0x04)
#        sending_data(0x02,0x04)
#        flag_special = 4
#    elif qipan[2][0] == 1 and (qipan[0][1]==2 or qipan[1][2]==2 ):
#        sending_data(0x02,0x04)
#        sending_data(0x02,0x04)
#        flag_special = 4
#    elif qipan[2][2] == 1 and (qipan[1][0]==2 or qipan[0][1]==2 ):
#        sending_data(0x02,0x04)
#        sending_data(0x02,0x04)
#        flag_special = 4
#    elif qipan[1][1] == 1 and (qipan[0][1] == 2 or qipan[1][0] == 2 or qipan[1][2] == 2 or qipan[2][1] == 2):
#        sending_data(0x02,0x05)
#        sending_data(0x02,0x05)
#        flag_special = 5



    return flag_special

# 根据人下棋对应的格子，补全qipan
# idx 1-9 下棋的格子序号，value 1 黑 2 白
def fill_qi(idx,value):
    global qipan

    if idx == 0:
        qipan[0][0] = value
    elif idx == 1:
        qipan[0][1] = value
    elif idx == 2:
        qipan[0][2] = value
    elif idx == 3:
        qipan[1][0] = value
    elif idx == 4:
        qipan[1][1] = value
    elif idx == 5:
        qipan[1][2] = value
    elif idx == 6:
        qipan[2][0] = value
    elif idx == 7:
        qipan[2][1] = value
    elif idx == 8:
        qipan[2][2] = value


# 机器下棋，并将结果发送至主控板
def move(role):
    global step
    step += 1
    x, y = computer_move(role)
    print("moving",x,y)
    qipan[x][y] = role
    sending_data(0x01,x*3+y+1)
    sending_data(0x01,x*3+y+1)
    sending_data(0x01,x*3+y+1)

# 下完棋后，扫描并填充棋盘
def scan_qi(color): #扫描棋盘
    global img,qipan
    img = sensor.snapshot().lens_corr(1.8)
    global lst_roi,threshold_W,threshold_B


    thB = threshold_B
    thW = threshold_W

    print("step",step)
    for r in lst_roi:
        img.draw_rectangle(r)
        i=0

    print(qipan)
    i=0
    for r in lst_roi:
        blobs_w = img.find_blobs([thB],roi=r)
        i+=1
        if blobs_w:
            blob_w = find_max(blobs_w)

            if blob_w.w()*blob_w.h()/r[2]*r[3]<0.4:
                continue
            print("w",i)
            fill_qi(i-1,1)
        blobs_w = img.find_blobs([thW],roi=r)
        if blobs_w:
            blob_w = find_max(blobs_w)

            if blob_w.w()*blob_w.h()/r[2]*r[3]<0.4:
                continue
            print("w",i)
            fill_qi(i-1,2)
    print(qipan)


    return 1


#    return 0

# 下完棋后，扫描并填充棋盘。对应模式为有悔棋或人为挪动棋子
def scan_qi1(color):
    global img,qipan
    img = sensor.snapshot().lens_corr(1.8)
    global lst_roi,threshold_W,threshold_B


    thB = threshold_B
    thW = threshold_W

    print("step",step)
#    for r in lst_roi:
#        img.draw_rectangle(r)
#        i=0
    for i in range(3):
        for j in range(3):
            olde_qipan[i][j] = qipan[i][j]
    i=0
    qipan = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for r in lst_roi:
        blobs_w = img.find_blobs([thB],roi=r)
        i+=1
        if blobs_w:
            blob_w = find_max(blobs_w)

            if blob_w.w()*blob_w.h()/r[2]*r[3]<0.4:
                continue
            print("w",i)
            fill_qi(i-1,1)
        blobs_w = img.find_blobs([thW],roi=r)
        if blobs_w:
            blob_w = find_max(blobs_w)

            if blob_w.w()*blob_w.h()/r[2]*r[3]<0.4:
                continue
            print("w",i)
            fill_qi(i-1,2)

    print("olde_qipan",olde_qipan)
    print("new_qipan",qipan)
    old_v = 0
    new_v = 0
    flag_ex = 0
    if color == 1:
        o_cnt = n_cnt = 0
        for i in range(3):
            for j in range(3):
                if olde_qipan[i][j] !=0:
                    o_cnt += 1
                if qipan[i][j] != 0:
                    n_cnt += 1
                if olde_qipan[i][j] != qipan[i][j]:
                    if olde_qipan[i][j] != 0:
                        old_v = i*3+j+1
                    elif  qipan[i][j] != 0:
                        new_v = i*3+j+1
                    flag_ex = 1
        if flag_ex == 1 and o_cnt == n_cnt:
            tmp = old_v*10+new_v
            print(old_v,new_v)
            sending_data(0x04,tmp)
            for i in range(3):
                for j in range(3):
                    qipan[i][j] = olde_qipan[i][j]
            return 1

    return 0




#---------------------------------------------------------
threshold_R = (6, 92, 11, 102, 1, 99)#(9, 82, 25, 98, -41, 80)#(9, 60, 2, 89, -32, 59)# (4, 45, -14, 70, -32, 67)
sqr_roi = 0
# 裁剪前原始图像左上角坐标
ox=39
oy=9
# 记录棋盘旋转角度
aa = 0
# 找到棋盘某色块列表中的最大色块
def find_max(blobs):
    max_size=0
    for blob in blobs:
        if blob[2]*blob[3] > max_size:
            max_blob=blob
            max_size = blob[2]*blob[3]
    return max_blob

# 完善棋盘的九个格子的中心坐标
def colors_shape(lst_k):

    global oy,ox,mode,sqr_roi,aa
    # 找到整个棋盘的大色块
    blobs=img.find_blobs([threshold_R],margin=30)

    # 用于确定棋盘是否旋转：1 不旋转，0旋转。
    flag_G=0
    if mode == 4 or mode == 5 or mode == 6:
        flag_G=1
    if blobs:
        b=find_max(blobs)
        sqr_roi = b.rect()
        img.draw_rectangle(b.rect(),color = (255, 255, 255))
#        img.draw_line(b.major_axis_line())
        # 得到整个棋盘的四个角点（但未确定四个角点对应的实际位置）
        lst1 = b.corners()

        # 通过比较四个角点的位置，确定四个角点的实际位置
        lst = [[0,0],[0,0],[0,0],[0,0]]
        for i in range(0,4):
            if lst1[i][0]<b.cx() and lst1[i][1]<b.cy():
                tmp=[0,0]
                tmp[0]=lst1[i][0]
                tmp[1]=lst1[i][1]
                lst[0] = tmp
            elif lst1[i][0]>b.cx() and lst1[i][1]<b.cy():
                tmp=[0,0]
                tmp[0]=lst1[i][0]
                tmp[1]=lst1[i][1]
                lst[1] = tmp
            elif lst1[i][0]<b.cx() and lst1[i][1]>b.cy():
                tmp=[0,0]
                tmp[0]=lst1[i][0]
                tmp[1]=lst1[i][1]
                lst[3] = tmp
            elif lst1[i][0]>b.cx() and lst1[i][1]>b.cy():
                tmp=[0,0]
                tmp[0]=lst1[i][0]
                tmp[1]=lst1[i][1]
                lst[2] = tmp

#        img.draw_circle(b.cx(),b.cy(),2)
#        print(lst1,lst,b.cx(),b.cy())
        # pz 为棋盘中心格子的中心坐标
        pz = [b.cx()-ox,b.cy()-oy]
        for t in lst:
            if t[0]==0 and t[1]==0:
                flag_G=1

        # 利用棋盘四个顶点的坐标，确定棋盘的旋转角度
        if flag_G == 0:
            # 将顶点坐标转换成裁剪后的坐标
            p0 = [lst[0][0]-ox,lst[0][1]-oy]
            p1 = [lst[1][0]-ox,lst[1][1]-oy]
            p2 = [lst[2][0]-ox,lst[2][1]-oy]
            p3 = [lst[3][0]-ox,lst[3][1]-oy]
    #        print(p0,p1,p2,p3)
            # 计算棋盘的旋转角度，并适当修正
            dx1 = p3[0] - p0[0]
            dy1 = p3[1] - p0[1]
            radian = math.atan2(dy1, dx1)
            tmp = math.degrees(radian)-90
            if tmp <0 :
                tmp -= 3
            else:
                tmp += 3
            tmp = round(tmp)
            aa = tmp

            h10 = [int(p0[0]+dx1/3),int(p0[1]+dy1/3)]
            h20 = [int(p0[0]+dx1*2/3),int(p0[1]+dy1*2/3)]

            dx2 = p1[0] - p0[0]
            dy2 = p1[1] - p0[1]
            s10 = [int(p0[0]+dx2/3),int(p0[1]+dy2/3)]
            s20 = [int(p0[0]+dx2*2/3),int(p0[1]+dy2*2/3)]
            h11 = [int(h10[0]+dx2),int(h10[1]+dy2)]
            h21 = [int(h20[0]+dx2),int(h20[1]+dy2)]
            s11 = [int(s10[0]+dx1),int(s10[1]+dy1)]
            s21 = [int(s20[0]+dx1),int(s20[1]+dy1)]


        # 利用棋盘四个顶点以及中心格子的坐标，以及棋盘每个格子的大小，确定棋盘每个格子的中心坐标
        if flag_G==1:
            lst_k[0] = [pz[0]-45,pz[1]-45]
            lst_k[1] = [pz[0],pz[1]-45]
            lst_k[2] = [pz[0]+45,pz[1]-45]
            lst_k[3] = [pz[0]-45,pz[1]]
            lst_k[4] = [pz[0],pz[1]]
            lst_k[5] = [pz[0]+45,pz[1]]
            lst_k[6] = [pz[0]-45,pz[1]+45]
            lst_k[7] = [pz[0],pz[1]+45]
            lst_k[8] = [pz[0]+45,pz[1]+45]
        else:
            if p0[0]<p3[0]:
                dirt = 3
            else:
                dirt=5
            dy=dy1/3
            dx=dx2/3
            #
            hz0 = [int(p0[0]+dx1/6),int(p0[1]+dy1/6)]
            hz1 = [int(p0[0]+dx1/2),int(p0[1]+dy1/2)]
            hz2 = [int(p0[0]+dx1*5/6),int(p0[1]+dy1*5/6)]
            lst_k[0] = [int(hz0[0]+dx2/6),int(hz0[1]+dy2/6)]
            lst_k[1] = [int(hz0[0]+dx2/2),int(hz0[1]+dy2/2)]
            lst_k[2] = [int(hz0[0]+dx2*5/6),int(hz0[1]+dy2*5/6)]
            lst_k[3] = [int(hz1[0]+dx2/6),int(hz1[1]+dy2/6)]
            lst_k[4] = [pz[0],pz[1]]
            lst_k[5] = [int(hz1[0]+dx2*5/6),int(hz1[1]+dy2*5/6)]
            lst_k[6] = [int(hz2[0]+dx2/6),int(hz2[1]+dy2/6)]
            lst_k[7] = [int(hz2[0]+dx2/2),int(hz2[1]+dy2/2)]
            lst_k[8] = [int(hz2[0]+dx2*5/6+dirt),int(hz2[1]+dy2*5/6)+dirt]



mode = 7
ren_end = 0 #对方下完棋
me_end = 0  #我(机器)方下完棋
role = -1   # 机器人下棋方 1黑 2白
rec = -1
flag_E = 0
scan = 0
# 储存九个格子（裁剪后）的中心坐标
lst_k=[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
# 储存九个格子检测棋子的roi（其大小要小于与实际格子，这样旋转后就不会受影响）
lst_roi = []

threshold_B =(0, 14, -22, 23, -30, 26)#(0, 11, -23, 23, -5, 22)
threshold_W =(56, 92, -34, 26, -35, 26)#(56, 97, -34, 23, -44, 25)# (69, 90, -35, 23, -49, 26)
# 和棋标志位
flag_special = 0

flag_Y = 0
flag_ex = 0
img = sensor.snapshot().lens_corr(1.8)
while(True):

    if uart.any():
        s = uart.read(2)
        print(s)
        if s.isdigit():
            rec = int(s)
            mode = rec
            sending_data(0x05,00)
            print("s",rec)
        scan = 0

    img = sensor.snapshot().lens_corr(1.8)
    img.draw_rectangle((ox,oy,250,240),color = (255, 255, 255))


    scan+=1
    if scan < 100:
        lst_roi = []
        colors_shape(lst_k)
        for lst in lst_k:
            x = lst[0]+ox-20
            y = lst[1]+oy-20
            lst_roi.append((x+10,y+15,15,15))
    if scan %10 == 0 and  mode == 3 and scan <150:
        sending_data(0x03,aa+45)

    lst_roi.reverse()
    for r in lst_roi:
        img.draw_rectangle(r)






    if mode == 4 and flag_E != 1:
        role = 1
        if step == 0:
            while True: # 等待输入第一步位置，由stm32控制下完第一步棋子，再将棋子发送至openmv
                img = sensor.snapshot().lens_corr(1.8)
                if uart.any():
                    s = uart.read(1)
                    print(s)
                    if s.isdigit():
                        num = int(s)
                        print("s" ,num)
                        fill_qi(num-1,1)
                        break
        else:
            move(role)
        while True: # 机械臂下完，me_end = 1
            if uart.any():
                s  = uart.read(2)
                if s.isdigit():
                    t = int(s)
                    if t == 10:
                        me_end = 1
                        break
        ren_end = 0
        print("step",step)
        if if_victory(0) != -1 or check_before(1) != -1:
            flag_E = 1
        if me_end == 1 and ren_end == 0:
            print("人在下棋")
            while True: # 人在下棋
                img = sensor.snapshot().lens_corr(1.8)
                if uart.any():
                    s  = uart.read(2)
                    if s.isdigit():
                        t = int(s)
                        if t == 11:
                            ren_end = 1
                            step += 1
                            break
            print("step", step)
            scan_qi(2)
            # 扫描棋盘 判断人下棋在什么位置，补全qipan
            me_end = 0
            if step == 2 and check_special() == 1:
                flag_E = 2

            elif if_victory(0) != -1 or check_before(1) != -1:
                flag_E = 1


    if mode == 5 and flag_E != 1:
        role = 2
        print("人在下棋")
        while True: # 人在下棋
            img = sensor.snapshot().lens_corr(1.8)
            for r in lst_roi:
                img.draw_rectangle(r)
                i=0
            if uart.any():
                s = uart.read(2)
                if s.isdigit():
                    t  = int(s)
                    print(t)
                    if t == 11:
                        ren_end = 1
                        step += 1
                        break
        print("step",step)
        scan_qi(1)
            # 扫描棋盘 判断人下棋在什么位置，补全qipan
        me_end = 0
#            if step == 2 and check_special() == 1:
#                flag_E = 2
        if if_victory(0) != -1 or check_before(1) != -1:
            flag_E = 1
        if me_end == 0 and ren_end == 1:
            move(role)
            while True: #机械臂下完，me_end = 1
                img = sensor.snapshot().lens_corr(1.8)
                for r in lst_roi:
                    img.draw_rectangle(r)
                    i=0
                if uart.any():
                    s = uart.read(2)
                    if s.isdigit():
                        t  = int(s)
                        if t == 10:
                            me_end = 1
                            break
            ren_end = 0
            print("step",step)
            if if_victory(0) != -1 or check_before(1) != -1:
                flag_E = 1


    if mode == 6 and flag_E != 1:
        role = 2
        print("人在下棋")
        while True: # 人在下棋
            img = sensor.snapshot().lens_corr(1.8)
            if uart.any():
                s = uart.read(2)
                if s.isdigit():
                    t  = int(s)
                    print(t)
                    if t == 11:
                        ren_end = 1
                        step += 1
                        break

        re = scan_qi1(1)
            # 扫描棋盘 判断人下棋在什么位置，补全qipan
        me_end = 0
        if re == 1:
            ren_end = 0
            me_end = 1
            step -= 1
        elif if_victory(0) != -1 or check_before(1) != -1:
            flag_E = 1
        if re != 1 and me_end == 0 and ren_end == 1:
            move(role)
            while True: #机械臂下完，me_end = 1
                img = sensor.snapshot().lens_corr(1.8)
                if uart.any():
                    s = uart.read(2)
                    if s.isdigit():
                        t  = int(s)
                        if t == 10:
                            me_end = 1
                            break
            ren_end = 0

            if if_victory(0) != -1 or check_before(1) != -1:
                flag_E = 1

