10 REM PC-BASIC test 
20 REM comparison operators
30 OPEN "OUTPUT.TXT" FOR OUTPUT AS 1
40 ON ERROR GOTO 10000
50 DEFINT A,B: A=-32768: B=-32766: GOSUB 1000
60 DEFINT A,B: A=-32767: B=-32766: GOSUB 1000
65 DEFINT A,B: A=32767: B=32766: GOSUB 1000
70 DEFINT A,B: A=32767: B=-32766: GOSUB 1000
75 DEFINT A,B: A=-32767: B=32766: GOSUB 1000
80 DEFINT A,B: A=-32768: B=32767: GOSUB 1000
90 DEFINT A,B: A=0: B=0: GOSUB 1000
100 DEFINT A,B: A=-1: B=0: GOSUB 1000
110 DEFINT A,B: A=0: B=-1: GOSUB 1000
120 DEFINT A,B: A=-0: B=0: GOSUB 1000
150 DEFSNG A,B: A=-32768: B=-32766: GOSUB 1000
160 DEFSNG A,B: A=-32767: B=-32766: GOSUB 1000
165 DEFSNG A,B: A=32767: B=32766: GOSUB 1000
170 DEFSNG A,B: A=32767: B=-32766: GOSUB 1000
175 DEFSNG A,B: A=-32767: B=32766: GOSUB 1000
180 DEFSNG A,B: A=-32768: B=32767: GOSUB 1000
200 DEFSNG A,B: A=0: B=0: GOSUB 1000
210 DEFSNG A,B: A=-1: B=0: GOSUB 1000
220 DEFSNG A,B: A=0: B=-1: GOSUB 1000
230 DEFSNG A,B: A=-0: B=0: GOSUB 1000
250 DEFDBL A,B: A=-32768: B=-32766: GOSUB 1000
260 DEFDBL A,B: A=-32767: B=-32766: GOSUB 1000
265 DEFDBL A,B: A=32767: B=32766: GOSUB 1000
270 DEFDBL A,B: A=32767: B=-32766: GOSUB 1000
275 DEFDBL A,B: A=-32767: B=32766: GOSUB 1000
280 DEFDBL A,B: A=-32768: B=32767: GOSUB 1000
300 DEFDBL A,B: A=0: B=0: GOSUB 1000
310 DEFDBL A,B: A=-1: B=0: GOSUB 1000
320 DEFDBL A,B: A=0: B=-1: GOSUB 1000
330 DEFDBL A,B: A=-0: B=0: GOSUB 1000
500 DEFSTR A,B: A="": B="": GOSUB 1000
510 DEFSTR A,B: A="A": B="": GOSUB 1000
520 DEFSTR A,B: A="A": B="AA": GOSUB 1000
530 DEFSTR A,B: A="AA": B="AB": GOSUB 1000
540 DEFSTR A,B: A="BA": B="AB": GOSUB 1000
550 DEFSTR A,B: A="A": B="1": GOSUB 1000
560 DEFSTR A,B: A="A": B=".": GOSUB 1000
999 END
1000 PRINT#1, A>B, A>=B, A=>B, A=B, A<>B, A<=B, A=<B, A<B
1010 RETURN
10000 PRINT#1, "Error:", ERR, ERL
10010 RESUME NEXT
