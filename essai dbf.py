
import dbf

file1 = r"H:\essai\central-keeper\test dbf\bdd.dbf"
#file1 = r"k:\essai\central-keeper\test dbf\bdd.dbf"
#db = dbf.Table(file1, "valeur N(10,0);prix N(18,0)")

db = dbf.Table(file1)
db.open(dbf.READ_WRITE)
db.append((45,56))


drec = {
	'valeur':100,
	'prix':110,
}


db.append(drec)
#db.close()

# with dbf.Table(file1) as db:
# 	db.open(dbf.READ_WRITE)
# 	db.append((30,30))

pass