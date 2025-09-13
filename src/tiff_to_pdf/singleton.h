#ifndef SINGLETON_H
#define SINGLETON_H

template <class T>
class Singleton{
	public:
		static T& instance(){
			static T ref;
			return ref;
		}
	protected:
		// hide these function so they cannot be called
		Singleton();
		~Singleton();
		Singleton(Singleton const &);
		Singleton& operator=(Singleton const &);
};

#endif
