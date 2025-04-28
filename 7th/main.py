import make_wav
import error

# 1) wav 파일 생성
text = input("wav 파일에 넣을 텍스트를 입력하세요: ")
print()
make_wav.make_audio(text)

# 3) 오류 검출 및 디코딩
error.restore_error_wav("normal.wav","error.wav")