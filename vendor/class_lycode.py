import re

class LYCode:
    def convert_string_to_utf32_chars(self, input_string):
        binary_string = ''.join(format(ord(char), '07b') for char in input_string)
        chunks = [binary_string[i:i+14] for i in range(0, len(binary_string), 14)]
        base_value = int('00000000000000000100111000000000', 2)
        utf32_chunks = []
        
        for chunk in chunks:
            chunk_value = int(chunk.ljust(14, '0'), 2)
            utf32_value = base_value + chunk_value
            utf32_chunks.append(format(utf32_value, '032b'))
        
        utf32_chars = []
        for utf32_chunk in utf32_chunks:
            decimal_value = int(utf32_chunk, 2)
            if decimal_value <= 0x10FFFF:
                utf32_chars.append(chr(decimal_value))
            else:
                utf32_chars.append('�')
        
        return ''.join(utf32_chars)

    def reverse_utf32_chars_to_string(self, utf32_string):
        binary_string = ''
        for char in utf32_string:
            decimal_value = ord(char)
            chunk_value = decimal_value - int('00000000000000000100111000000000', 2)
            binary_string += format(chunk_value, '014b')
        
        original_chunks = [binary_string[i:i+7] for i in range(0, len(binary_string), 7)]
        original_string = ''.join(chr(int(chunk, 2)) for chunk in original_chunks if int(chunk, 2) > 0)
        return original_string

    def encode(self, file_unique_id, file_id, bot_name, file_type):
        file_unique_id_enc = self.convert_string_to_utf32_chars(file_unique_id)
        file_id_enc = self.convert_string_to_utf32_chars(file_id)
        bot_name_enc = self.convert_string_to_utf32_chars(bot_name)

        if file_type == "document":
            tail = "文"
        elif file_type == "photo":
            tail = "图"
        elif file_type == "video":
            tail = "影"
        else:
            tail = ""

        return f"正{file_unique_id_enc}太{file_id_enc}密{bot_name_enc}{tail}"

    def decode(self, text):
        pattern = r'^\u6b63([\u4e00-\u9fa5]{5,10})\u592a([\u4e00-\u9fa5]{34,100})\u5bc6([\u4e00-\u9fa5]{5,10})[\u6587\u56fe\u5f71]$'
        match = re.match(pattern, text)
        row = {'file_unique_id': '', 'file_id': '', 'bot': '', 'file_type': ''}
        if match:
            last_char = text[-1]
            if last_char == "文":
                file_type = "document"
            elif last_char == "图":
                file_type = "photo"
            elif last_char == "影":
                file_type = "video"
            else:
                file_type = ""

            row['file_unique_id'] = self.reverse_utf32_chars_to_string(match.group(1))
            row['file_id'] = self.reverse_utf32_chars_to_string(match.group(2))
            row['bot'] = self.reverse_utf32_chars_to_string(match.group(3))
            row['file_type'] = file_type
        return row


