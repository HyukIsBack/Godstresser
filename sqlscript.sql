CREATE DATABASE panel default CHARACTER SET UTF8;
use panel;
CREATE TABLE usertbl(
    userid VARCHAR(45) PRIMARY KEY NOT NULL,
    userpw VARCHAR(45) NOT NULL,
    expired VARCHAR(45),
    userplan VARCHAR(45),
    concurrent INT,
    running INT,
    userdate DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=INNODB;
CREATE TABLE codetbl(
    code VARCHAR(45) PRIMARY KEY NOT NULL, #코드번호
    codeplan VARCHAR(45) NOT NULL
) ENGINE=INNODB;

INSERT INTO usertbl
(userid, userpw)
VALUES('admin', '1234');

INSERT INTO codetbl
(code, codeplan)
VALUES('TESTCODE', 'Bronze');
# 코드 , 플랜 (플랜은 맨앞에만 대문자 ex) Silver, Gold )

select * from usertbl;
select * from codetbl;

