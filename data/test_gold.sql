SELECT avg(age) ,  min(age) ,  max(age) FROM singer WHERE country  =  'France'	concert_singer
SELECT T1.title FROM course AS T1 JOIN prereq AS T2 ON T1.course_id  =  T2.course_id GROUP BY T2.course_id HAVING count(*)  =  2	college_2