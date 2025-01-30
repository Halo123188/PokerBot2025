import random
import joblib

prob_list = [0, 1/6, 2/6, 1/6, 1/6, 1/6] #list of size 6
test_list = [0,0,0,0,0,0]
def test_probabilities(n=5000, test_list= test_list):
    for _ in range(n):
        num = random.random()
        if num >=0 and num < prob_list[0]:
            test_list[0] +=1
            # print('fold')
        elif num >= prob_list[0] and num < (prob_list[0] + prob_list[1]):
            test_list[1] +=1
            # print('call')
        elif num >= (prob_list[0] + prob_list[1]) and num < (prob_list[0] + prob_list[1] + prob_list[2]):
            test_list[2] +=1
            # print('check')
        elif num >= (prob_list[0] + prob_list[1] + prob_list[2]) and num < (prob_list[0] + prob_list[1] + prob_list[2] + prob_list[3]):
            test_list[3] +=1
            # print('betmin') #bmin, min-1x pot
        elif num >= (prob_list[0] + prob_list[1] + prob_list[2] + prob_list[3]) and num < (prob_list[0] + prob_list[1] + prob_list[2] + prob_list[3]+prob_list[4]):
            test_list[4] +=1
            # print('betmid') #bmid, 1x pot-2x pot
        elif num >= (prob_list[0] + prob_list[1] + prob_list[2] + prob_list[3]+prob_list[4]) and num < 1:
            test_list[5] +=1
            # print('betmax') #bmax, 2x pot- all in
        else:
            raise Exception("Something went wrong with the probability distribution")

test_probabilities()
print(sum(test_list))
print(test_list)

# bb_data = joblib.load('./python_skeleton/training_data/big_blind_infoset_file.pkl')
# sb_data = joblib.load('./python_skeleton/training_data/small_blind_infoset_file.pkl')
# print(sb_data)
