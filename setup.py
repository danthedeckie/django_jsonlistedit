from setuptools import setup

setup(
    name='django_jsonlistedit',
    version='0.0.1',
    packages=['django_jsonlistedit'],
    license='MIT',
    include_package_data=True,
    author='Daniel Fairhead',
    author_email='danthedeckie@gmail.com',
    url='https://github.com/danthedeckie/django_jsonlistedit/',
    description='Core field type and setup for using jsonlistedit to store JSON lists in a text field in django',
    long_description=open('README.rst').read(),
    install_requires=['django >= 1.11.0'],
    python_requires='>=3.4',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
    ],
)    
