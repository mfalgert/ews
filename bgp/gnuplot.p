#!/usr/bin/gnuplot

load './common.p'
set terminal pdf dl 1.5 enhanced dashed size 3.0, 2.0 font "Helvetica,15"

set ylabel 'CDF' offset 2.5,0
set xlabel 'Updates per AT' offset 0,1

set xtics 10 offset 0,0.5
set mxtics 5
set xrange[0:30]

set ytics 0.2
set mytics 2
set yrange[0:1]

set key bottom right samplen 2
set style line 1 lt rgb(darkred) lw 2
set style line 2 lt rgb(darkgreen) lw 2
set style line 3 lt rgb(black) lw 2

set output "CDF.pdf"
N_LINES = system("wc -l < 00/146.228.1.3-AS1836")

plot \
  "< (cut -d ' ' -f 1  at-1/00/146.228.1.3-AS1836 | sort -n)" using 1:(($0/N_LINES)) with lines lt 1 title "AT of 1", \
  "< (cut -d ' ' -f 1  at-30/00/146.228.1.3-AS1836 | sort -n)" using 1:(($0/N_LINES)) with lines lt 2 title "AT of 30"
