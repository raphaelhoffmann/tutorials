#!/bin/sh

cd $(dirname $0)/..

pwd

if [ ! -d "tmp" ]; then
  mkdir tmp
fi

if [ ! -d "images" ]; then
  mkdir images
fi

cd tmp
cat <<EOF > eq1.tex
\documentclass[preview]{standalone}
\begin{document}
$ d_j = ( w_{1,j}, w_{2,j}, \ldots, w_{t,j} )$
\end{document}
EOF

pdflatex eq1
convert -density 600 eq1.pdf -quality 90 eq1.png
mv eq1.png ../images

cat <<EOF > eq2.tex
\documentclass[preview]{standalone}
\begin{document}
$\cos \theta = \frac{d_1 \cdot d_2}{d_2}$
\end{document}
EOF

pdflatex eq2
convert -density 600 eq2.pdf -quality 90 eq2.png
mv eq2.png ../images



