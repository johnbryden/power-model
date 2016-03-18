# Copyright John Bryden under GPL3 license 
#
# However, don't publish any results generated using this code without
# my permisison

from pylab import *
from collections import namedtuple
import sys
import argparse

# this is a unidirectional link between two people
class Link:

    def __init__(self, outPerson, inPerson, linkValueToOut, linkValueToIn):
        self.outPerson = outPerson
        self.inPerson = inPerson
        self.linkValueToOut = linkValueToOut
        self.linkValueToIn = linkValueToIn


# a person (or node) in the network
class Person:
    
    def __init__ (self,personid):

        # this the id of the person
        self.personid = personid

        # the person has a list of its Links to other people
        self.outgoingLinks=list()
        # they also have a dictionary (id -> link) of Links from others
        self.incomingLinks=dict()

        # this is the initial status of the person
        self.status=1.0
        # this is to record the status which is incoming from others
        self.incomingStatus = 0

    def show (self):
        print "I am person",self.personid
        print "I have status",self.status
        print "Incoming status is",self.incomingStatus
        for link in self.outgoingLinks:
            print "->",link.inPerson.personid
        print self.numIncomingLinks,"incoming links"
        print

    def getNumLinks(self):
        return len(self.incomingLinks)+len(self.outgoingLinks)
        
    def updateStatus(self):
        status += statusChange
        statusChange = 0

    # This function calculates the outgoing link which is of least
    # value to the individual
    def getWorstLink(self, addIncomingValueIfLinkIsMutual=False):
        worstlink = None
        worstValue= 1e500
        for link in self.outgoingLinks:
            linkvalue = link.linkValueToOut
            if addIncomingValueIfLinkIsMutual:
                if link.inPerson.personid in self.incomingLinks:
                    linkvalue += self.incomingLinks[link.inPerson.personid].linkValueToIn
            if linkvalue < worstValue:
                worstValue = link.linkValueToOut
                worstlink = link

        return worstlink


class Population:
    # Manages a dictionary (id->person) of people and a list of links
    # between them
    

    def __init__(self, numPeople,numLinks,r=0.2,q=0.9):

        self.numPeople = 20
        self.numLinks  = 5


        self.q = q
        self.r = r

        self.people = dict()
        self.links = list()

        # to record some data which will later be plotted
        self.numlinksvsstatus=list()

        for i in range (0,self.numPeople):
            self.people[i] = Person(i)

        # generate a random network
        for pid,person in self.people.items():
            avoidPeople=[person.personid,]
            for j in range (0,self.numLinks):
                linkedPerson=self.findIndividualToLinkTo(avoidPeople)
                avoidPeople.append(linkedPerson.personid)
                newlink = Link(outPerson = person, inPerson = linkedPerson, linkValueToOut = 0.0, linkValueToIn = 0.0)
                self.links.append (newlink)
                person.outgoingLinks.append(newlink)
                linkedPerson.incomingLinks[person.personid]=newlink


    # functions for getting random individuals
    def getRandomPerson (self):
        return self.people[randint(self.numPeople)]

    def findIndividualToLinkTo (self, avoidPeopleIDs):
        newPerson = self.getRandomPerson()
        while newPerson.personid in avoidPeopleIDs:
            newPerson = self.getRandomPerson()

        return newPerson
        

    def showPeople(self):
        for pid,person in self.people.items():
            person.show()

    def updateStatuses(self):
        # reset link values
        for link in self.links:
            link.linkValueToIn = 0.0
            link.linkValueToOut = 0.0
        
        
        for link in self.links:
            outPerson = link.outPerson
            inPerson = link.inPerson

            # Each person takes a proportion r of their status (which
            # will be deducted later) and divides that amongst their
            # links.
            outStatusForLink = self.r*outPerson.status/float(outPerson.getNumLinks())
            inStatusForLInk = self.r*inPerson.status/float(inPerson.getNumLinks())
         
            # The status attributed to each link is divided unevenly
            # between the pair - with a proportion q going to the
            # person who's getting their link
            linkValue = outStatusForLink+inStatusForLInk
            link.linkValueToIn = linkValue*self.q
            link.linkValueToOut = linkValue*(1.0-self.q)

            outPerson.incomingStatus += link.linkValueToOut
            inPerson.incomingStatus += link.linkValueToIn

        for pid,person in self.people.items():
            person.status += person.incomingStatus-self.r*person.status
            person.incomingStatus = 0
            
    def outputLinksVersusStatus (self):
        # I want to generate a heat map of status / num links
        for pid,person in self.people.items():
            numlinks = person.getNumLinks()
            status = person.status
            self.numlinksvsstatus.append((numlinks,status))

#            self.numlinksvsstatus_output.write(str(numlinks)+' '+str(status)+'\n')
    
    def getStatuses (self):
        statuses = []
        for pid,person in self.people.items():
            statuses.append(person.status)
        return statuses

    def rewireLinks (self):

        for pid,person in self.people.items():
            #                print "Person",person.personid,"rewiring from",

            worstLink = person.getWorstLink()
            personBeingRemoved = worstLink.inPerson
            #                print personBeingRemoved.personid,

            # Remove this link from the old person's links
            personBeingRemoved.incomingLinks.pop(pid)

            # In this version, it won't rewire to any of those
            # already linked to (including the person being
            # removed)
            avoidPeople = [person.personid,]
            for link in person.outgoingLinks:
                avoidPeople.append(link.inPerson.personid)

            newPerson = self.findIndividualToLinkTo(avoidPeople)

            #update the link and give it to the new person
            worstLink.inPerson = newPerson

            newPerson.incomingLinks[person.personid]=worstLink

            # this checks if there is a bug where an invidual has
            # too many incoming linsk
            if len(newPerson.incomingLinks) == self.numPeople:
                print person.personid
                print avoidPeople
                print newPerson.personid
                print personBeingRemoved.personid
                print worstLink.outPerson.personid, worstLink.inPerson.personid
                #               print "to",newPerson.personid

    # for debugging purposes
    def findAnomalousIndividual (self):
        for pid,person in self.people.items():
            if person.getNumLinks() > (self.numLinks+self.numPeople-1):
                print "Person: ",person.personid
                for link in self.links:
                    if link.outPerson == person or link.inPerson == person:
                        print link.outPerson.personid,"->",link.inPerson.personid

                        

print sys.argv

parser = argparse.ArgumentParser()
parser.add_argument ('-q',type=float,default=0.5, help="q: level of inequality in the model")
parser.add_argument ('-r',type=float,default=0.2, help="r: rate that status is contributed to others")
parser.add_argument ('-n',type=int,default=20, help="number of people")
parser.add_argument ('-l',type=int,default=5, help="number of links")
parser.add_argument ('--show',action="store_true", help="Show graph")

args = parser.parse_args()

print args

qval = float(args.q)
rval = float(args.r)
nval = int(args.n)
lval = int(args.l)

population = Population(nval,lval,rval,qval)

data=[]

for t in range(0,100000):
    population.updateStatuses()
    population.rewireLinks()
    population.outputLinksVersusStatus()
    population.findAnomalousIndividual()
    statuses=population.getStatuses()
    data.append(statuses)
    
adata=array(data)
figure(1,figsize=(20,10))
subplot (1,2,1)
hold(False)
plot (adata,alpha=0.5)
xlabel('time')
ylabel('status')
subplot (1,2,2)
hold(False)
lvs=array(population.numlinksvsstatus)
plot (lvs[:,0],lvs[:,1],'o',alpha=0.01, markersize=30)
xlabel('Number of links')
ylabel('Status')
savefig('q_'+str(qval)+'_r_'+str(rval)+'_n_'+str(nval)+'_l_'+str(lval)+'_fig.png')
if args.show:
    show()



