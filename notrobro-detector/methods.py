from abc import ABC, abstractmethod


# abstract class, inherited by each Detector Method
class DetectorMethod(ABC):

    @abstractmethod
    def get_common_intro(self, l1, l2):
        pass

    @abstractmethod
    def get_common_outro(self, l1, l2):
        pass


# tries each method until a result is found or no methods left
class AllMethods(DetectorMethod):
    methods = []

    def __init__(self):
        self.methods.append(AllMatchMethod())
        self.methods.append(LongestContinousMethod())


    def get_common_intro(self, l1, l2):
        result = []
        i = 0
        while(i < len(self.methods) and len(result) == 0):
            result = self.methods[i].get_common_intro(l1,l2)
            i = i + 1

        return result

    def get_common_outro(self, l1, l2):
        result = []
        i = 0
        while(i < len(self.methods) and len(result) == 0):
            result = self.methods[i].get_common_outro(l1,l2)
            i = i + 1

        return result


# all_match method
class AllMatchMethod(DetectorMethod):

    def get_common_intro(self, l1, l2):
        common = []
        for i, element in enumerate(l1):
            try:
                ind = l2.index(element)
                common.append((i, ind))
            except:
                pass
        return common

    def get_common_outro(self, l1, l2):
        common = []
        for i, element1 in enumerate(l1):
            for j, element2 in enumerate(l2):
                if (element1-element2) <= 5:
                    if len(common) != 0 and common[-1][1] < j:
                        common.append((i, j))
                        break
                    elif len(common) == 0:
                        common.append((i, j))
                        break
        return common


# longest_common method
class LongestContinousMethod(DetectorMethod):

    def get_common_intro(self, l1, l2):
        subarray = []
        indices = []
        len1, len2 = len(l1), len(l2)
        for i in range(len1):
            for j in range(len2):
                temp = 0
                cur_array = []
                cur_indices = []
                # hamming distance
                while ((i+temp < len1) and (j+temp < len2) and (l1[i+temp]-l2[j+temp]) <= 30):
                    cur_array.append(l2[j+temp])
                    cur_indices.append((i+temp, j+temp))
                    temp += 1
                if (len(cur_array) > len(subarray)):
                    subarray = cur_array
                    indices = cur_indices
        # return subarray, indices
        return indices

    def get_common_outro(self, l1, l2):
        # not implemented for this method yet
        return []

