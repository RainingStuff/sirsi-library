# sirsi-library
parses output from Sirsi into a more useful format for some person on reddit

run it by doing something like:
python main.py "Sirsi WorkFlows Text Report.txt" -o SirsiFinalOutput.txt --sort_order FICTION NONFICTION GRAPHICNVL

first arguement is the sirsi report

-o
output file name

--sort_order
Specifies the library layout 

One thing I did not do is add line breaks for new page stuff, I am not sure how to do that as I assume that is specific to the paper size and margin settings you have in your printer settings.
