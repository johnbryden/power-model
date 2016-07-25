#include <iostream>
#include <fstream>
#include <map>
#include <list>
#include <set>

#include "boost/random.hpp"

using namespace std;

typedef boost::mt19937 base_rng_type;
typedef boost::mt19937& base_rng_ref;
base_rng_type RNG;
typedef boost::uniform_int<> distribution_type_int;
typedef boost::uniform_real<> distribution_type_real;
typedef boost::poisson_distribution<int,double> distribution_type_poisson;
typedef boost::normal_distribution<double> distribution_type_normal;

typedef boost::variate_generator<base_rng_ref, distribution_type_int > gen_type_int;
typedef boost::variate_generator<base_rng_ref, distribution_type_real > gen_type_real;
typedef boost::variate_generator<base_rng_ref, distribution_type_poisson > gen_type_poisson;
typedef boost::variate_generator<base_rng_ref, distribution_type_normal > gen_type_normal;




class Person;

class Link
{
public:

  Link ()
    : linkValueToOriginator (0.0), linkValueToReceiver (0.0)
  {}

  shared_ptr < Person > originator;
  shared_ptr < Person > receiver;
  double linkValueToOriginator;
  double linkValueToReceiver;
};

typedef shared_ptr<Link> RLink;


class Person 
{
public:

  int personId;

  double status;
  double deltaStatus;

  map <int,shared_ptr< Link > > originatedLinks;
  map <int,shared_ptr< Link > > receivedLinks;

  Person (int id)
    : personId(id), status(1.0), deltaStatus(0.0)
  {}
    
  void show (ostream & ostr) {
    ostr << "I am person " << personId << endl;
    ostr << "I have status " << status << endl;
    ostr << "Received status is " << deltaStatus << endl;
    for (auto & entry:originatedLinks) 
      ostr << "->" << entry.second->receiver->personId << endl;
    for (auto & entry:receivedLinks) 
      ostr << entry.second->originator->personId << "->" << endl;
    ostr << receivedLinks.size() << "received links" << endl;
    ostr << endl;
  }

  double getNumLinks () {
    return (originatedLinks.size() + receivedLinks.size());
  }


  RLink getWorstLink () {
    RLink worstLink;
    double worstValue=1e90;

    for (auto & entry:originatedLinks) {
      RLink link = entry.second;
      if (link->linkValueToOriginator <worstValue) {
	worstValue = link->linkValueToOriginator;
	worstLink = link;
      }
    }

    if (!worstLink) {
      cerr << "Didn't find a worst link" << endl;
      show (cerr);
    }

    assert (worstLink);
    return worstLink;
  }
};
  
typedef shared_ptr<Person> RPerson;


  
class Population 
{
public:

  base_rng_type rng;

  int numPeople;
  int originatedLinksPerPerson;
  
  double q;
  double r;
  double w;

  map <int,RPerson > people;
  list <RLink > links;

  vector<int> allPeople;

  double maxStatus;

  Population () 
    : numPeople (30),originatedLinksPerPerson(3),
      q(0.9),r(0.2),w(1.0),maxStatus(0.0)
  {
    rng.seed(1001);
  }

  void initialise () {
    for (int i = 0; i< numPeople; i++) {
      people[i] = RPerson (new Person (i));
    }

    for (int i = 0; i< numPeople; i++) {
      allPeople.push_back (i);
    }

    for (auto & entry:people) {
      set<int> avoidPeopleIDs;
      RPerson originator = entry.second;
      avoidPeopleIDs.insert(entry.first);
      for (int j = 0; j<originatedLinksPerPerson; j++) {
	RPerson receiver = findIndividualToLinkTo (avoidPeopleIDs);
	avoidPeopleIDs.insert (receiver->personId);
	RLink newLink = RLink(new Link());
	newLink->originator = entry.second;
	newLink->receiver= receiver;
	links.push_back(newLink);
	originator->originatedLinks[receiver->personId] = newLink;
	receiver->receivedLinks[originator->personId] = newLink;
      }
    }
  }

  RPerson getRandomPerson () {
    gen_type_int gen (rng,distribution_type_int(0,numPeople-1));
    int personId = gen();
    RPerson person = people[personId];
    assert (person);
    return person;
  }

  RPerson findIndividualToLinkTo (set<int> & avoidPeopleIDs) {
    assert ((int)avoidPeopleIDs.size() < numPeople);
    RPerson candidate;
    if (avoidPeopleIDs.size() > numPeople*0.95 && false) {
      vector<int> remainingPeople;
      remainingPeople.reserve (numPeople-avoidPeopleIDs.size()+1);
      set_difference (allPeople.begin(),allPeople.end(),
		      avoidPeopleIDs.begin(),avoidPeopleIDs.end(),
		      std::inserter(remainingPeople, remainingPeople.begin()));
      gen_type_int gen (rng,distribution_type_int(0,remainingPeople.size()-1));
      int newid = remainingPeople[gen()];
      assert (avoidPeopleIDs.find(newid) == avoidPeopleIDs.end());
      candidate =people[newid];
    }
    else {
      candidate = getRandomPerson();
      while (avoidPeopleIDs.find(candidate->personId) != avoidPeopleIDs.end()) {
	candidate = getRandomPerson();
      }
    }
    return candidate;
  }

  void showPeople (ostream & ostr) {
    for (auto & entry:people) {
      entry.second->show(ostr);
    }
  }

  void updateStatuses () {
    double statusSum = 0; 
    for (auto & entry:people)  {
      RPerson person = entry.second;
      statusSum += person->status;
      person->deltaStatus = 0.0;
    }
    
    for (auto & link:links) {
      link->linkValueToReceiver = 0.0;
      link->linkValueToOriginator = 0.0;
    }

    for (auto & link:links) {
      RPerson originator = link->originator;
      RPerson receiver = link->receiver;
      
      double statusForLinkFromOriginator = r*originator->status/double(originator->getNumLinks());
      double statusForLinkFromReceiver = r*receiver->status/double(receiver->getNumLinks());
      
      double linkValue = statusForLinkFromReceiver+statusForLinkFromOriginator;
      link->linkValueToReceiver = linkValue * q;
      link->linkValueToOriginator = linkValue * (1.0-q);

      originator->deltaStatus += link->linkValueToOriginator;
      receiver->deltaStatus += link->linkValueToReceiver;
    }
    
    //    cout << statusSum << " ";
    statusSum = 0; 

    for (auto & entry:people) {
      RPerson person = entry.second;
      person->status += person->deltaStatus-r*person->status;
      statusSum += person->status;
      person->deltaStatus = 0.0;
    }
    //    cout << statusSum << endl;
  }

  void rewireLinks () {
    gen_type_real gen (distribution_type_real(rng));
    for (auto & entry:people) {
      RPerson person = entry.second;
      int pid = entry.first;
      if (w== 1.0 || rand()<w) {
	

	if (person->getNumLinks() +1 < numPeople) {
	  // we'll avoid anyone we're already linked to
	  set<int> avoidPeopleIDs;
	  avoidPeopleIDs.insert(pid);

	  for (auto & linkedTo:person->originatedLinks) 
	    avoidPeopleIDs.insert(linkedTo.first);
	  
	  for (auto & linkedTo:person->receivedLinks) 
	    avoidPeopleIDs.insert(linkedTo.first);
	  
	  RLink worstLink = person->getWorstLink();
	  RPerson receiverToBeRemoved = worstLink->receiver;
	  
	  receiverToBeRemoved->receivedLinks.erase(pid);
	  person->originatedLinks.erase(receiverToBeRemoved->personId);
	  
	  RPerson newPerson = findIndividualToLinkTo(avoidPeopleIDs);
	  worstLink->receiver = newPerson;
	
	  newPerson->receivedLinks[pid] = worstLink;
	  person->originatedLinks[newPerson->personId] = worstLink;
	}
      }
    }
    //    showPeople(cout);
  }
  
  void outputStatuses(ostream & dataout) {
    maxStatus = 0.0;
    for (auto & entry:people) {
      dataout << entry.second->status << " ";
      maxStatus=max(maxStatus,entry.second->status);
    }
    dataout << endl;
  }
  
};

int main (int argc, char ** argv) {

  
  double q = 0.7;

  if (argc>1) 
    q = stod(string(argv[1]));

  ofstream dataout ("statuses_q_"+to_string(q)+"_.dat");
  Population pop;

  pop.q = q;
  pop.initialise();

  //  pop.showPeople(cout);

  for (int t = 0; t<100000; t++) {
    pop.updateStatuses();
    pop.rewireLinks();
    pop.outputStatuses(dataout);
  }

  cout << q <<" " << pop.maxStatus << endl;

}
