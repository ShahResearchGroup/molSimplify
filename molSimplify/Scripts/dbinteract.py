# Written by Tim Ioannidis for HJK Group
# Dpt of Chemical Engineering, MIT

######################################################
######## This script interacts with chemical  ########
#####  databases performing similarity search   ######
########  and screening. It uses openbabel. ##########
######################################################

# import custom modules
from geometry import *
from io import *
from molSimplify.Classes.globalvars import *
# import std modules
import os, sys
import pybel, openbabel

######################################################
### get directories for ChEMBL/emolecules database ###
######################################################
def setupdb(dbselect):
    globs = globalvars()
    flag = False
    flag = globs.check_db()
    if flag:
        dbdir = os.path.relpath(globs.chemdbdir)+'/'
        # get files in directory
        dbfiles = os.listdir(dbdir)
        # search for db files
        dbmatches = [dbf for dbf in dbfiles if dbselect.lower() in dbf.lower()]
        dbsdf = [dbm for dbm in dbmatches if '.sdf' in dbm]
        dbfs = [dbm for dbm in dbmatches if '.fs' in dbm]
        if len(dbsdf)==0:
            print dbselect+' sdf database file missing from '+dbdir+'. Please make sure file '+dbselect+'.sdf is there..'
            dbf1 = False
        else:
            dbf1 = dbdir+dbsdf[0]
        if len(dbfs)==0:
            print dbselect+' fastsearch database file missing from '+dbdir+'. Please make sure file '+dbselect+'.fs is there, it speeds up search significantly..'
            dbf2 = False
        else:
            dbf2 = dbdir+dbfs[0]
    else:
            print globs.chemdbdir+' does not exist. Please make sure the file name is recorded in ~/.molSimplify'
            dbf1 = False
            dbf2 = False
    return [dbf1,dbf2]

#######################
#### Print filters ####
#######################
def obfilters():
    s = " A list of available filters for Database searching is listed below.\n"
    s += """
    -abonds    Number of aromatic bonds
    -atoms    Number of atoms
    -bonds    Number of bonds
    -cansmi    Canonical SMILES
    -cansmiNS    Canonical SMILES without isotopes or stereo
    -dbonds    Number of double bonds
    -formula    Chemical formula
    -HBA1    Number of Hydrogen Bond Acceptors 1 (JoelLib)
    -HBA2    Number of Hydrogen Bond Acceptors 2 (JoelLib)
    -HBD    Number of Hydrogen Bond Donors (JoelLib)
    -InChI    IUPAC InChI identifier
    -InChIKey    InChIKey
    -L5    Lipinski Rule of Five
    -logP    octanol/water partition coefficient
    -MR    molar refractivity
    -MW    Molecular Weight filter
    -nF    Number of Fluorine Atoms
    -s    SMARTS filter
    -sbonds    Number of single bonds
    -smarts    SMARTS filter
    -tbonds    Number of triple bonds
    -title    For comparing a molecule's title
    -TPSA    topological polar surface area 
    """
    s += "\n Similarity search can be performed using 4 fingerprints. Available fingerprints are:\n"
    s += """
    -FP2    Indexes linear fragments up to 7 atoms. (Default)
    -FP3    SMARTS patterns specified in the file /usr/local/share/openbabel/*/patterns.txt
    -FP4    SMARTS patterns specified in the file /usr/local/share/openbabel/*/SMARTS_InteLigand.txt
    -MACCS    SMARTS patterns specified in the file /usr/local/share/openbabel/*/MACCS.txt
    """
    return s

#############################
#### Check for screening ####
#############################
def checkscr(args):
    scr = '"'
    if args.dbsmarts:
        scr += "s'"+args.dbsmarts+"' &"
    if args.dbatoms:
        nts = args.dbatoms.split('<')
        if nts[0]!='':
            scr += " atoms>"+nts[0]+" &"
        if nts[1]!='':
            scr += " atoms<"+nts[1]+" &"
    if args.dbbonds:
        nts = args.dbbonds.split('<')
        if nts[0]!='':
            scr += " bonds>"+nts[0]+" &"
        if nts[1]!='':
            scr += " bonds<"+nts[1]+" &"
    if args.dbarbonds:
        nts = args.dbarbonds.split('<')
        if nts[0]!='':
            scr += " abonds>"+nts[0]+" &"
        if nts[1]!='':
            scr += " abonds<"+nts[1]+" &"
    if args.dbsbonds:
        nts = args.dbsbonds.split('<')
        if nts[0]!='':
            scr += " sbonds>"+nts[0]+" &"
        if nts[1]!='':
            scr += " sbonds<"+nts[1]+" &"
    if args.dbmw:
        nts = args.dbmw.split('<')
        if nts[0]!='':
            scr += " MW>"+nts[0]+" &"
        if nts[1]!='':
            scr += " MW<"+nts[1]+" &"
    if scr=='"':
        scr = ''
    else:
        scr = scr[:-2]+'"'
    return scr

#################################
##### Gets similar molecules ####
#################################
def getsimilar(smi,nmols,dbselect,finger,squery):
    #######################################
    ##   smi: pybel reference smiles     ##
    ##   nmols: number of similar ones   ##
    ## dbselect: database to be searched ##
    #######################################
    ## get database files
    [dbsdf,dbfs] = setupdb(dbselect)
    globs = globalvars()
    if globs.osx:
        obab = '/usr/local/bin/babel'
    else:
        obab = 'babel'
    if dbfs:
        com = obab+' '+dbfs+' simres.smi -xf'+finger+' -s"'+smi+'" -at'+nmols+' --filter '+squery
    else:
        com = obab+' '+dbsdf+' simres.smi -xf'+finger+' -s"'+smi+'" -at'+nmols+' --filter '+squery
    ## perform search using bash commandline
    print(com)
    res = mybash(com)
    print res
    ## check output and print error if nothing was found
    if ('errors' in res):
        ss = 'No matches were found in DB. Log info:\n'+res
        print ss
        return ss,True
    else:
        return 'simres.smi',False

##################################
##### Strip salts from smiles ####
##################################
def stripsalts(fname,nres):
    acc0 = ['H','B','C','N','O','F','P','S','Cl','Br','I','Si']
    acc1 = ['O-','F-','Cl-','Br-','I-','C@@H','C@H','N+','C@']
    accepted = acc0+acc1
    if glob.glob(fname):
        f = open(fname,'r')
        s = f.read().splitlines()
        f.close()
    else:
        return 0
    f = open(fname,'w')
    for i,ss in enumerate(s):
        ss = ss.split('\t')[0]
        ls = ss.split('[')
        for l in ls:
            if ']' in l:
                lq = l.split(']')[0]
                if lq not in accepted:
                    lq0 = '.['+lq+']'
                    lq1 = '['+lq+'].'
                    if lq0 in ss:
                        ss = ss.replace(lq0,'')
                    elif lq1 in ss:
                        ss = ss.replace(lq1,'')
        ss = ss.split('.')[0]
        f.write(ss+'\n')
    f.close()
    return 0

#######################################
##### Maximal dissimilarity search ####
#######################################
def dissim(outf,n):
	globs = globalvars()
	if globs.osx:
		obab = '/usr/local/bin/babel'
	else:
		obab = 'babel'
	# generate fs of original hit list
	mybash(obab+' -ismi simres.smi -osdf -O tmp.sdf')
	mybash(obab+' tmp.sdf -ofs')
	# number of hits
        sim=[];
        with open('simres.smi','r') as f:
               for lines in f:
                   sim.append(lines.strip("\n"))
	numcpds = len(sim)
	# pick last element of list
	mybash('obabel tmp.sdf -O 1.smi -f '+str(numcpds)+' -l'+str(numcpds))
	if n > 1:
		# find most dissimilar structure
		for i in range(n-1):
			# initialize list of total similarities
			simsum = [0] * int(numcpds)
			# compute total similarity of each dissimilar structure with hit list
			for j in range(i+1):
				a = mybash('obabel '+str(j+1)+'.smi tmp.sdf -ofpt')
				a = a.splitlines()
				a = [s.split('= ') for s in a]
				a = [item for sublist in a for item in sublist]
                                aa = []
                                for k in a:
                                    try:
                                        aa.append(float(k))
                                    except:
                                        pass
                                a = aa
				simsum = [x + y for x,y in zip(simsum,a)]
			# pick most dissimilar structure by greedily minimizing total similarity
			mostdissim = simsum.index(min(simsum))
			print('most dissimilar '+str(mostdissim))
			mybash('obabel tmp.sdf -O '+str(i+2) +'.smi -f '+str(mostdissim+1)+' -l'+str(mostdissim+1))
	# combine results into one file
	f = open('dissimres.smi','w')
	for i in range(n):
		ff = open(str(i+1)+'.smi','r')
		s = ff.read().splitlines()
		ff.close()
		f.write(s[0]+'\n')
		os.remove(str(i+1)+'.smi')
	f.close()
	return 0

####################################
#### Matches initial SMARTS and ####
####  defines connection atoms  ####
####################################
def matchsmarts(smarts,outf,catoms,nres):
    # read output file to pybel mol
    mols = list(pybel.readfile('smi',outf))
    sm = pybel.Smarts(smarts)
    f = open(outf,'r')
    s = f.read().splitlines()
    f.close()
    f = open(outf,'w')
    for i,mol in enumerate(mols):
        smm = sm.findall(mol)
        if len(smm) > 0:
            pmatch = smm[0]
            cc = ''
            for at in catoms:
                att = at-1 # indexing
                cc += str(pmatch[att])+','
            if i < nres:
                f.write(s[i]+' '+cc[:-1]+'\n')
                #f.write(s[i]+'\n')
    f.close()
    return 0

####################################
##### Main driver for db search ####
####################################
def dbsearch(rundir,args,globs):
    if globs.osx:
        obab = '/usr/local/bin/obabel'
    else:
        obab = 'obabel'
    if args.gui:
        from Classes.mWidgets import mQDialogErr
        from Classes.mWidgets import mQDialogWarn
        from Classes.mWidgets import mQDialogInf
    ### in any case do similarity search over indexed db ###
    outf = args.dboutputf if args.dboutputf else 'simres.smi' # output file
    cwd = os.getcwd()
    os.chdir(globs.homedir)
    ### convert to SMILES/SMARTS if file
    if not args.dbbase:
        if args.gui:
            qqb = mQDialogWarn('Warning',"No database file found within "+globs.chemdbdir+'. Search not possible.')
            qqb.setParent(args.gui.DBWindow)
        print "No database file found within "+globs.chemdbdir+'. Search not possible.'
        return True
    if args.dbsim:
        if '.smi' in args.dbsim:
            if glob.glob(args.dbsim):
                f = open(args.dbsim,'r')
                smistr = f.read()
                f.close()
            else:
                print 'File '+args.dbsim+' not existing. Check your input.'
                print 'Similarity search terminating..'
                return True
        elif ('.mol' in args.dbsim or '.xyz' in args.dbsim):
            if glob.glob(args.dbsim):
                ftype = args.dbsim.split('.')[-1]
                pymol = pybel.readfile(ftype,args.dbsim).next()
                smistr = pymol.write("smi")
            else:
                print 'File '+args.dbsim+' not existing. Check your input.'
                print 'Similarity search terminating..'
                return True
        else:
            smistr = args.dbsim
    elif args.dbsmarts:
        if '.smi' in args.dbsmarts:
            if glob.glob(args.dbsmarts):
                f = open(args.dbsmarts,'r')
                smistr = f.read()
                f.close()
            else:
                print 'File '+args.dbsmarts+' not existing. Check your input.'
                print 'Similarity search terminating..'
                return 1
        elif ('.mol' in args.dbsmarts or '.xyz' in args.dbsmarts):
            if glob.glob(args.dbsmarts):
                ftype = args.dbsmarts.split('.')[-1]
                pymol = pybel.readfile(ftype,args.dbsmarts).next()
                smistr = pymol.write("smi")
            else:
                print 'File '+args.dbsmarts+' not existing. Check your input.'
                print 'Similarity search terminating..'
                return True
        else:
            smistr = args.dbsmarts
    else:
        # get database
        [dbsdf,dbfs] = setupdb(args.dbbase)
        # convert to smiles and print to output
        if globs.osx:
            cmd = "/usr/local/bin/obabel "+dbsdf+" -f0 -l100 -o"+outf[-3:]+" -O "+outf
        else:
            cmd = obab+" "+dbsdf+" -f0 -l100 -o"+outf[-3:]+" -O "+outf
        t = mybash(cmd)
        os.rename(outf,args.rundir+'/'+outf)
        print t
        return False
    ### now run filtering if needed
    squery = checkscr(args)
    ### run similarity search anyway ###
    nmols = '10000' if not args.dbresults else args.dbresults
    finger = 'FP2' if not args.dbfinger else args.dbfinger
    if int(nmols) > 3000 and args.gui:
        qqb = mQDialogInf('Warning',"Database search is going to take a few minutes. Please wait..OK?")
        qqb.setParent(args.gui.DBWindow)
    outputf,flag = getsimilar(smistr,nmols,args.dbbase,finger,squery)
    if flag:
        if args.gui:
            qqb = mQDialogWarn('Warning',"No matches found in search..")
            qqb.setParent(args.gui.DBWindow)
        print "No matches found in search.."
        return True
    # strip metals and clean-up, remove duplicates etc
    flag = stripsalts(outf,args.dbresults)
    cmd = obab+" -ismi "+outf+" -osmi -O "+outf+" --unique"
    t = mybash(cmd)
    print t
    # check if defined connection atoms
    if args.dbcatoms:
        catoms = [int(a) for a in args.dbcatoms]
    else:
        catoms = [1]
    # do pattern matching
    nres = 50 if not args.dbresults else int(args.dbresults)
    flag = matchsmarts(smistr,outf,catoms,nres)
    ### maximal dissimilarity search
    if args.dbdissim:
        dissim(outf,int(args.dbdissim))
        flag = stripsalts('dissimres.smi',args.dbdissim)
        flag = matchsmarts(smistr,'dissimres.smi',catoms,int(args.dbdissim))
        #print(flag)
        os.rename('dissimres.smi',args.rundir+'/dissimres.smi')
    os.rename(outf,args.rundir+'/'+outf)
    os.chdir(cwd)
    return False
        
        
