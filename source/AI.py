import math
import sys
import source.utils as utils

sys.setrecursionlimit(1500)

N = 15 # kích thước bàn cờ 15x15

class GomokuAI():
    def __init__(self, depth=3):
        self.depth = depth # độ sâu mặc định là 3
        self.boardMap = [[0 for j in range(N)] for i in range(N)]
        self.currentI = -1
        self.currentJ = -1
        self.nextBound = {} # lưu các nước đi có thể kiểm tra (i,j)
        self.boardValue = 0 

        self.turn = 0 
        self.lastPlayed = 0
        self.emptyCells = N * N
        self.patternDict = utils.create_pattern_dict() # từ điển chứa tất cả các mẫu và điểm tương ứng
        
        self.zobristTable = utils.init_zobrist()
        self.rollingHash = 0
        self.TTable = {}

    # Vẽ bàn cờ dưới dạng chuỗi
    def drawBoard(self):
        '''
        Trạng thái:
        0 = ô trống (.)
        1 = AI (x)
        -1 = người chơi (o)
        '''
        for i in range(N):
            for j in range(N):
                if self.boardMap[i][j] == 1:
                    state = 'x'
                if self.boardMap[i][j] == -1:
                    state = 'o'
                if self.boardMap[i][j] == 0:
                    state = '.'
                print('{}|'.format(state), end=" ")
            print()
        print() 
    
    # Kiểm tra nước đi có nằm trong bàn cờ và ô đó có trống không
    def isValid(self, i, j, state=True):
        '''
        Nếu state=True, kiểm tra cả ô đó có trống không
        Nếu state=False, chỉ kiểm tra nước đi có nằm trong bàn cờ không
        '''
        if i<0 or i>=N or j<0 or j>=N:
            return False
        if state:
            if self.boardMap[i][j] != 0:
                return False
            else:
                return True
        else:
            return True

    # Đặt trạng thái cho một vị trí, "đánh" nước đi
    def setState(self, i, j, state):
        '''
        Trạng thái:
        0 = ô trống (.)
        1 = AI (x)
        -1 = người chơi (o)
        '''
        assert state in (-1,0,1), 'The state inserted is not -1, 0 or 1'
        self.boardMap[i][j] = state
        self.lastPlayed = state


    def countDirection(self, i, j, xdir, ydir, state):
        count = 0
        # kiểm tra tối đa 4 bước theo một hướng nhất định
        for step in range(1, 5): 
            if xdir != 0 and (j + xdir*step < 0 or j + xdir*step >= N): # đảm bảo nước đi trong bàn cờ
                break
            if ydir != 0 and (i + ydir*step < 0 or i + ydir*step >= N):
                break
            if self.boardMap[i + ydir*step][j + xdir*step] == state:
                count += 1
            else:
                break
        return count

    # Kiểm tra có 5 quân liên tiếp không (theo 4 hướng)
    def isFive(self, i, j, state):
        # 4 hướng: ngang, dọc, 2 đường chéo
        directions = [[(-1, 0), (1, 0)], \
                      [(0, -1), (0, 1)], \
                      [(-1, 1), (1, -1)], \
                      [(-1, -1), (1, 1)]]
        for axis in directions:
            axis_count = 1
            for (xdir, ydir) in axis:
                axis_count += self.countDirection(i, j, xdir, ydir, state)
                if axis_count >= 5:
                    return True
        return False

    # Trả về tất cả các nước đi con (i,j) trong trạng thái bàn cờ dựa trên bound
    # Sắp xếp tăng dần theo giá trị của chúng
    def childNodes(self, bound):
        for pos in sorted(bound.items(), key=lambda el: el[1], reverse=True):
            yield pos[0]

    # Cập nhật biên cho các nước đi mới có thể thực hiện dựa trên nước vừa đánh
    def updateBound(self, new_i, new_j, bound):
        # loại bỏ vị trí vừa đánh
        played = (new_i, new_j)
        if played in bound:
            bound.pop(played)
        # check in all 8 directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1), (-1, -1), (1, 1)]
        for dir in directions:
            new_col = new_j + dir[0]
            new_row = new_i + dir[1]
            if self.isValid(new_row, new_col)\
                    and (new_row, new_col) not in bound: 
                bound[(new_row, new_col)] = 0
    
    # Hàm này kiểm tra sự xuất hiện của mẫu quanh vị trí (i, j) (ngang, dọc, chéo)
    def countPattern(self, i_0, j_0, pattern, score, bound, flag):
        '''
        pattern = key của patternDict --> tuple các mẫu với độ dài khác nhau
        score = value của patternDict --> điểm số tương ứng với mẫu
        bound = dict với (i, j) là key và giá trị ô là value
        flag = +1 nếu muốn cộng điểm, -1 nếu muốn trừ điểm khỏi bound
        '''
        # Đặt hướng đơn vị
        directions = [(1, 0), (1, 1), (0, 1), (-1, 1)]
        # Chuẩn bị cột, hàng, độ dài, số lượng
        length = len(pattern)
        count = 0

        # Lặp qua 4 hướng
        for dir in directions:
            # Tìm số ô (tối đa 5) có thể lùi lại mỗi hướng để kiểm tra mẫu
            if dir[0] * dir[1] == 0:
                steps_back = dir[0] * min(5, j_0) + dir[1] * min(5, i_0)
            elif dir[0] == 1:
                steps_back = min(5, j_0, i_0)
            else:
                steps_back = min(5, N-1-j_0, i_0)
            # Điểm bắt đầu đầu tiên sau khi xác định số bước lùi lại
            i_start = i_0 - steps_back * dir[1]
            j_start = j_0 - steps_back * dir[0]

            # Duyệt qua tất cả các mẫu có thể trong một hàng/cột/chéo
            z = 0
            while z <= steps_back:
                # Lấy điểm bắt đầu mới
                i_new = i_start + z*dir[1]
                j_new = j_start + z*dir[0]
                index = 0
                # Tạo danh sách lưu các vị trí trống phù hợp với mẫu
                remember = []
                # Kiểm tra từng ô trong hàng/cột/chéo có giống mẫu không
                while index < length and self.isValid(i_new, j_new, state=False) \
                        and self.boardMap[i_new][j_new] == pattern[index]: 
                    if self.isValid(i_new, j_new):
                        remember.append((i_new, j_new)) 
                    
                    i_new = i_new + dir[1]
                    j_new = j_new + dir[0]
                    index += 1

                # Nếu tìm được một mẫu
                if index == length:
                    count += 1
                    for pos in remember:
                        # Kiểm tra pos đã có trong bound chưa
                        if pos not in bound:
                            bound[pos] = 0
                        bound[pos] += flag*score  # Sẽ cập nhật phần trăm tốt hơn ở evaluate()
                    z += index
                else:
                    z += 1

        return count
    
    # Hàm này nhận giá trị bàn cờ hiện tại và nước đi dự định, trả về giá trị sau khi đi nước đó
    # Ý tưởng là tính sự khác biệt số lượng mẫu quanh vị trí kiểm tra, rồi cộng vào giá trị hiện tại
    def evaluate(self, new_i, new_j, board_value, turn, bound):
        '''
        board_value = giá trị bàn cờ cập nhật ở mỗi minimax và khởi tạo là 0
        turn = [1, -1] lượt AI hoặc người chơi
        bound = dict các ô trống có thể đánh cùng điểm số tương ứng
        '''
        value_before = 0
        value_after = 0
        
        # Kiểm tra từng mẫu trong patternDict
        for pattern in self.patternDict:
            score = self.patternDict[pattern]
            # For every pattern, count have many there are for new_i and new_j
            # and multiply them by the corresponding score
            value_before += self.countPattern(new_i, new_j, pattern, abs(score), bound, -1)*score
            # Make the move then calculate value_after
            self.boardMap[new_i][new_j] = turn
            value_after += self.countPattern(new_i, new_j, pattern, abs(score), bound, 1) *score
            
            # Delete the move
            self.boardMap[new_i][new_j] = 0

        return board_value + value_after - value_before

    ### Thuật toán MiniMax với cắt tỉa AlphaBeta ###
    def alphaBetaPruning(self, depth, board_value, bound, alpha, beta, maximizingPlayer):

        if depth <= 0 or (self.checkResult() != None):
            return  board_value # Đánh giá tĩnh
        
        # Bảng chuyển vị có dạng {hash: [score, depth]}
        if self.rollingHash in self.TTable and self.TTable[self.rollingHash][1] >= depth:
            return self.TTable[self.rollingHash][0] # trả về giá trị bàn cờ đã lưu trong TTable
        
        # AI là người tối đa hóa
        if maximizingPlayer:
            # Khởi tạo giá trị max
            max_val = -math.inf

            # Duyệt qua tất cả các node con có thể
            for child in self.childNodes(bound):
                i, j = child[0], child[1]
                # Tạo bound mới với giá trị cập nhật
                # và đánh giá vị trí nếu thực hiện nước đi
                new_bound = dict(bound)
                new_val = self.evaluate(i, j, board_value, 1, new_bound)
                
                # Thực hiện nước đi và cập nhật zobrist hash
                self.boardMap[i][j] = 1
                self.rollingHash ^= self.zobristTable[i][j][0] # chỉ số 0 cho nước đi của AI

                # Cập nhật bound dựa trên nước đi mới (i,j)
                self.updateBound(i, j, new_bound) 

                # Đánh giá vị trí ở depth-1 và đến lượt đối thủ
                eval = self.alphaBetaPruning(depth-1, new_val, new_bound, alpha, beta, False)
                if eval > max_val:
                    max_val = eval
                    if depth == self.depth: 
                        self.currentI = i
                        self.currentJ = j
                        self.boardValue = eval
                        self.nextBound = new_bound
                alpha = max(alpha, eval)

                # Hoàn tác nước đi và cập nhật lại zobrist hashing
                self.boardMap[i][j] = 0 
                self.rollingHash ^= self.zobristTable[i][j][0]
                
                del new_bound
                if beta <= alpha: # cắt tỉa
                    break

            # Cập nhật bảng chuyển vị
            utils.update_TTable(self.TTable, self.rollingHash, max_val, depth)

            return max_val

        else:
            # Khởi tạo giá trị min
            min_val = math.inf
            # Duyệt qua tất cả các node con có thể
            for child in self.childNodes(bound):
                i, j = child[0], child[1]
                # Tạo bound mới với giá trị cập nhật
                # và đánh giá vị trí nếu thực hiện nước đi
                new_bound = dict(bound)
                new_val = self.evaluate(i, j, board_value, -1, new_bound)

                # Thực hiện nước đi và cập nhật zobrist hash
                self.boardMap[i][j] = -1 
                self.rollingHash ^= self.zobristTable[i][j][1] # chỉ số 1 cho nước đi của người chơi

                # Cập nhật bound dựa trên nước đi mới (i,j)
                self.updateBound(i, j, new_bound)

                # Đánh giá vị trí ở depth-1 và đến lượt đối thủ
                eval = self.alphaBetaPruning(depth-1, new_val, new_bound, alpha, beta, True)
                if eval < min_val:
                    min_val = eval
                    if depth == self.depth: 
                        self.currentI = i 
                        self.currentJ = j
                        self.boardValue = eval 
                        self.nextBound = new_bound
                beta = min(beta, eval)
                
                # Hoàn tác nước đi và cập nhật lại zobrist hashing
                self.boardMap[i][j] = 0 
                self.rollingHash ^= self.zobristTable[i][j][1]

                del new_bound
                if beta <= alpha: # cắt tỉa
                    break

            # Cập nhật bảng chuyển vị
            utils.update_TTable(self.TTable, self.rollingHash, min_val, depth)

            return min_val

    # Đặt nước đi đầu tiên của AI ở (7,7) - trung tâm bàn cờ
    def firstMove(self):
        self.currentI, self.currentJ = 7,7
        self.setState(self.currentI, self.currentJ, 1)

    # Kiểm tra trò chơi đã kết thúc chưa và trả về người thắng nếu có
    # nếu không, nếu không còn ô trống thì hòa
    def checkResult(self):
        if self.isFive(self.currentI, self.currentJ, self.lastPlayed) \
            and self.lastPlayed in (-1, 1):
            return self.lastPlayed
        elif self.emptyCells <= 0:
            # hòa
            return 0
        else:
            return None
    
    def getWinner(self):
        if self.checkResult() == 1:
            return 'Gomoku AI! '
        if self.checkResult() == -1:
            return 'Người chơi! '
        else:
            return 'Không ai'
