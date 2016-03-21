# This is an example of the data that application creation exists. 

app_dict = {
    "job":
        [{
            "type":"createApplication",
            "account":"dev",
            "application":{
                "cloudProviders":"aws",
                "name":"devopstest",
                "email":"devops@example.com",
                "platformHealthOnlyShowOverride": False
              },
          "user":"Jenkins"
          },
          {
              "type":"createApplication",
              "account":"stage",
              "application":{
                  "cloudProviders":"aws",
                  "name":"devopstest",
                  "email":"devops@example.com",
                  "platformHealthOnlyShowOverride": False
                  },
              "user":"Jenkins"
           {
              "type":"createApplication",
              "account":"prod",
              "application":{
                  "cloudProviders":"aws",
                  "name":"devopstest",
                  "email":"devops@example.com",
                  "platformHealthOnlyShowOverride": False
                  },
              "user":"Jenkins"
              }

   }
          ],
    "application":"devopstest",
    "description":"Create Application: devopstest"
}
