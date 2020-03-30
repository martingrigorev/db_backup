#!/bin/sh
# 1 - Настраиваем переменные
FILE=minime.sql.`date +"%Y%m%d"`
DBSERVER=127.0.0.1
DATABASE=XXX
USER=XXX
PASS=XXX

# 2 - Удаляем старое
unalias rm     2> /dev/null
rm ${FILE}     2> /dev/null
rm ${FILE}.gz  2> /dev/null

# 3 - Выполняем дамп
mysqldump --opt --user=${USER} --password=${PASS} ${DATABASE} > ${FILE}

# 4 - Архивируем
gzip $FILE

# 5 - показываем результат
echo "${FILE}.gz was created:"
ls -l ${FILE}.gz
